"""
Orquestador de la conversacion: implementa el loop de function-calling de
OpenAI, ejecuta las tools de dominio contra SQLite, y valida cualquier
emision de UI contra el esquema A2UI antes de dejarla salir hacia el
frontend.

Este es el unico lugar del backend que "habla" con el LLM.
"""
from __future__ import annotations
import json
import logging
from uuid import uuid4
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .client import get_client, get_model
from . import mcp_client
from .system_prompt import build_system_prompt
from .tool_specs import OPENAI_TOOLS
from ..models import ConversationTurn, InterfaceHistory, SessionState
from ..schemas.a2ui import A2UIScreen, A2UIClarification, A2UIEnvelope
from ..schemas.chat import ChatTextResponse

logger = logging.getLogger("banorte.orchestrator")

MAX_TOOL_ITERATIONS = 6
MAX_HISTORY_MESSAGES = 24

ALLOWED_STAGE_TRANSITIONS = {
    "idle": {"intent", "generated"},
    "intent": {"intent", "generated"},
    "generated": {"generated", "interaction", "confirmation", "result"},
    "interaction": {"interaction", "confirmation", "result"},
    "confirmation": {"interaction", "result"},
    "result": {"intent", "generated"},
}

STAGE_TO_STATE = {
    "intent": "UNDERSTANDING_INTENT",
    "generated": "GENERATED_VIEW",
    "interaction": "INTERACTION",
    "confirmation": "CONFIRMATION",
    "result": "COMPLETED",
}


def _history_intent(tool_names: list[str], stage_label: str) -> str:
    intent_by_tool = {
        "get_portfolio": "view_portfolio",
        "get_investment_cashflows": "view_cashflows",
        "calculate_performance": "view_performance",
        "compare_investments": "compare_investments",
        "simulate_investment": "simulate_investment",
        "confirm_investment": "confirm_investment",
        "set_investment_profile": "set_investment_profile",
    }
    for name in tool_names:
        if name in intent_by_tool:
            return intent_by_tool[name]
    return (stage_label or "investment_view").strip().lower().replace(" ", "_")


def _record_interface_history(
    db: Session,
    user_id: int,
    user_prompt: str | None,
    payload: A2UIScreen | A2UIClarification,
    tool_names: list[str],
    tool_args: dict,
    data_snapshot: dict,
) -> None:
    intent = _history_intent(tool_names, getattr(payload, "stage_label", ""))
    db.add(InterfaceHistory(
        user_id=user_id,
        title=getattr(payload, "title", None) or getattr(payload, "question", "Interfaz de inversiones")[:80],
        user_prompt=user_prompt,
        intent=intent,
        tool_names=tool_names,
        tool_args=tool_args,
        data_snapshot=data_snapshot,
        a2ui_payload=payload.model_dump(mode="json"),
    ))
    state = db.get(SessionState, user_id)
    if state is None:
        state = SessionState(user_id=user_id)
        db.add(state)
    state.flow_id = state.flow_id or str(uuid4())
    state.active_intent = intent
    state.context_json = {
        "activeModule": "investments",
        "intent": intent,
        "toolNames": tool_names,
        "lastPrompt": user_prompt,
    }
    db.commit()


def _history(db: Session, user_id: int) -> list[dict]:
    rows = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.user_id == user_id)
        .order_by(ConversationTurn.id.desc())
        .limit(MAX_HISTORY_MESSAGES)
        .all()
    )
    messages = [json.loads(row.content) for row in reversed(rows)]
    # No podemos iniciar el contexto en medio de un bloque assistant/tool.
    # Recortamos hasta el primer mensaje de usuario para conservar un historial
    # valido para Chat Completions y evitar que errores antiguos condicionen
    # indefinidamente solicitudes nuevas.
    while messages and messages[0].get("role") != "user":
        messages.pop(0)
    return messages


def _append_history(db: Session, user_id: int, message: dict) -> None:
    db.add(ConversationTurn(
        user_id=user_id,
        role=message["role"],
        content=json.dumps(message, ensure_ascii=False),
    ))
    db.commit()


def reset_history(db: Session, user_id: int) -> None:
    db.query(ConversationTurn).filter(ConversationTurn.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(SessionState).filter(SessionState.user_id == user_id).delete(
        synchronize_session=False
    )
    db.commit()


def _run_domain_tool(db: Session, user_id: int, name: str, tool_input: dict) -> dict:
    return mcp_client.call_domain_tool(name, user_id, tool_input)


def _build_ui_response(name: str, tool_input: dict) -> A2UIEnvelope | None:
    """Valida la salida del LLM contra el esquema A2UI. Si falla, regresa None
    para que el llamador pueda decidir un fallback en vez de romper el cliente."""
    try:
        if name == "emit_screen":
            screen = A2UIScreen(**tool_input)
            return A2UIEnvelope(payload=screen)
        if name == "emit_clarification":
            clarification = A2UIClarification(**tool_input)
            return A2UIEnvelope(payload=clarification)
    except ValidationError as e:
        logger.warning("Salida de %s no valido contra esquema A2UI: %s", name, e)
        return None
    return None


def _fallback_envelope(reason: str) -> A2UIEnvelope:
    """Pantalla de aclaracion generica cuando el LLM produce algo invalido.
    Preferimos degradar a una pregunta simple antes que mandar UI rota."""
    return A2UIEnvelope(payload=A2UIClarification(
        id="fallback-clarify",
        question="No logre armar esa pantalla correctamente. ¿Puedes darme un poco "
                  "mas de detalle sobre lo que quieres ver?",
        input_mode="free_text",
    ))


def _force_fallback_state(db: Session, user_id: int, envelope: A2UIEnvelope) -> None:
    """Sincroniza SessionState con la pantalla de fallback que SI se le manda
    al usuario cuando una transicion es rechazada o la salida del LLM no pasa
    la validacion A2UI. Sin esto, el FSM se queda apuntando al estado previo
    (p.ej. "idle") mientras el cliente ya esta viendo una aclaracion de tipo
    "intent", y CUALQUIER intento posterior de avanzar se rechaza tambien
    (el usuario queda atascado). El fallback es siempre una pregunta segura y
    reversible, asi que se acepta incondicionalmente, sin pasar por la tabla
    de transiciones (esa tabla protege contra saltos indebidos del LLM, no
    contra esta red de seguridad)."""
    payload = envelope.payload
    state = db.get(SessionState, user_id)
    if state is None:
        state = SessionState(user_id=user_id)
        db.add(state)
    state.current_stage = payload.stage_kind
    state.current_state = STAGE_TO_STATE[payload.stage_kind]
    state.active_module = "investments"
    state.last_screen_id = payload.id
    state.last_screen_payload = payload.model_dump(mode="json")
    state.pending_action = None
    db.commit()


def _accept_ui_transition(
    db: Session, user_id: int, envelope: A2UIEnvelope
) -> bool:
    payload = envelope.payload
    state = db.get(SessionState, user_id)
    current_stage = state.current_stage if state else "idle"
    new_stage = payload.stage_kind

    if new_stage not in ALLOWED_STAGE_TRANSITIONS.get(current_stage, set()):
        logger.warning(
            "Transicion A2UI no permitida para usuario %s: %s -> %s",
            user_id,
            current_stage,
            new_stage,
        )
        return False

    if state is None:
        state = SessionState(user_id=user_id)
        db.add(state)

    payload_dict = payload.model_dump(mode="json")
    state.current_stage = new_stage
    state.current_state = STAGE_TO_STATE[new_stage]
    state.active_module = "investments"
    state.last_screen_id = payload.id
    state.last_screen_payload = payload_dict
    state.pending_action = None

    if new_stage == "confirmation" and isinstance(payload, A2UIScreen):
        actions = [
            action
            for component in payload.components
            for action in component.actions
        ] + payload.footer_actions
        tools = sorted({
            action.tool
            for action in actions
            if action.requires_confirmation or action.requires_biometric
        })
        if tools:
            state.pending_action = {"screen_id": payload.id, "tools": tools}

    db.commit()
    return True


def run_turn(
    db: Session,
    user_id: int,
    user_full_name: str,
    active_categories: list[str],
    user_message: str | None,
) -> ChatTextResponse | A2UIEnvelope:
    """Ejecuta un turno completo: agrega el mensaje del usuario (si hay),
    corre el loop de tool-use hasta que el LLM emita UI o texto plano."""
    history = _history(db, user_id)
    if user_message is not None:
        user_entry = {"role": "user", "content": user_message}
        _append_history(db, user_id, user_entry)
        history.append(user_entry)

    state = db.get(SessionState, user_id)
    system = build_system_prompt(
        active_categories,
        user_full_name,
        {
            "activeModule": state.active_module if state else "investments",
            "currentState": state.current_state if state else "READY",
            "currentStage": state.current_stage if state else "idle",
            "activeIntent": state.active_intent if state else None,
            "context": state.context_json if state else {},
        },
    )
    client = get_client()
    requested_prompt = user_message
    turn_tool_names: list[str] = []
    turn_tool_args: dict = {}
    turn_data_snapshot: dict = {}

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.chat.completions.create(
            model=get_model(),
            max_tokens=2000,
            messages=[{"role": "system", "content": system}, *history],
            tools=OPENAI_TOOLS,
            # La experiencia de este modulo es UI generativa: incluso una
            # aclaracion debe salir como A2UI. Esto evita que el modelo ignore
            # el catalogo y responda solo texto ante una consulta valida.
            tool_choice="required",
        )

        message = response.choices[0].message
        tool_calls = message.tool_calls or []

        # Guardamos la respuesta del asistente tal cual (puede tener texto y/o tool_calls)
        assistant_entry = {"role": "assistant", "content": message.content}
        if tool_calls:
            assistant_entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in tool_calls
            ]
        _append_history(db, user_id, assistant_entry)
        history.append(assistant_entry)

        if not tool_calls:
            # Respuesta en texto plano (p.ej. fuera de dominio, o charla simple)
            text = (message.content or "").strip() or "¿En que mas te puedo ayudar?"
            return ChatTextResponse(payload=text)

        # Puede haber una tool de UI y/o varias tools de datos en la misma vuelta.
        ui_call = next((tc for tc in tool_calls if tc.function.name in ("emit_screen", "emit_clarification")), None)
        domain_calls = [tc for tc in tool_calls if tc.function.name not in ("emit_screen", "emit_clarification")]

        for tc in domain_calls:
            tool_input = json.loads(tc.function.arguments or "{}")
            result = _run_domain_tool(db, user_id, tc.function.name, tool_input)
            turn_tool_names.append(tc.function.name)
            turn_tool_args[tc.function.name] = tool_input
            turn_data_snapshot[tc.function.name] = result
            tool_entry = {
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            }
            _append_history(db, user_id, tool_entry)
            history.append(tool_entry)

        if ui_call:
            tool_input = json.loads(ui_call.function.arguments or "{}")
            envelope = _build_ui_response(ui_call.function.name, tool_input)
            accepted = envelope is not None and _accept_ui_transition(db, user_id, envelope)
            # Cerramos el tool_call con un ack para mantener el historial valido
            tool_entry = {
                "role": "tool",
                "tool_call_id": ui_call.id,
                "content": json.dumps({"delivered": accepted}),
            }
            _append_history(db, user_id, tool_entry)
            history.append(tool_entry)
            if accepted:
                _record_interface_history(
                    db=db,
                    user_id=user_id,
                    user_prompt=requested_prompt,
                    payload=envelope.payload,
                    tool_names=turn_tool_names,
                    tool_args=turn_tool_args,
                    data_snapshot=turn_data_snapshot,
                )
                return envelope
            fallback = _fallback_envelope("validacion o transicion fallida")
            _force_fallback_state(db, user_id, fallback)
            return fallback

        # Solo hubo tools de datos: los resultados ya quedaron en el historial;
        # seguimos el loop para que el modelo decida el siguiente paso
        # (normalmente emit_screen).

    fallback = _fallback_envelope("limite de iteraciones alcanzado")
    _force_fallback_state(db, user_id, fallback)
    return fallback


def run_action_result(
    db: Session,
    user_id: int,
    user_full_name: str,
    active_categories: list[str],
    tool: str,
    args: dict,
) -> ChatTextResponse | A2UIEnvelope:
    """
    Ejecuta directamente una accion disparada por un click en un componente
    generado (botones, sliders, selects). La accion se corre de forma
    deterministica en el backend -> el resultado se inyecta a la conversacion
    como si fuera un tool_result, y dejamos que el LLM decida la siguiente
    pantalla (confirmacion, resultado final, mas detalle, etc.).
    """
    result = _run_domain_tool(db, user_id, tool, args)
    synthetic_message = f"[resultado de accion: {tool}] {json.dumps(result, ensure_ascii=False)}"
    return run_turn(db, user_id, user_full_name, active_categories, synthetic_message)
