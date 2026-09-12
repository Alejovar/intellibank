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
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .client import get_client, get_model
from .system_prompt import build_system_prompt
from .tool_specs import OPENAI_TOOLS
from .tools import TOOL_REGISTRY
from ..models import ConversationTurn, SessionState
from ..schemas.a2ui import A2UIScreen, A2UIClarification, A2UIEnvelope
from ..schemas.chat import ChatTextResponse

logger = logging.getLogger("banorte.orchestrator")

MAX_TOOL_ITERATIONS = 6

ALLOWED_STAGE_TRANSITIONS = {
    "idle": {"intent", "generated"},
    "intent": {"intent", "generated"},
    "generated": {"generated", "interaction", "confirmation", "result"},
    "interaction": {"interaction", "confirmation", "result"},
    "confirmation": {"interaction", "result"},
    "result": {"intent", "generated"},
}


def _history(db: Session, user_id: int) -> list[dict]:
    rows = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.user_id == user_id)
        .order_by(ConversationTurn.id)
        .all()
    )
    return [json.loads(row.content) for row in rows]


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
    fn = TOOL_REGISTRY.get(name)
    if not fn:
        return {"error": f"tool desconocida: {name}"}
    try:
        return fn(db=db, user_id=user_id, **tool_input)
    except TypeError as e:
        logger.exception("Argumentos invalidos para tool %s", name)
        return {"error": f"argumentos invalidos para {name}: {e}"}
    except Exception as e:  # noqa: BLE001
        logger.exception("Error ejecutando tool %s", name)
        return {"error": str(e)}


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

    system = build_system_prompt(active_categories, user_full_name)
    client = get_client()

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.chat.completions.create(
            model=get_model(),
            max_tokens=2000,
            messages=[{"role": "system", "content": system}, *history],
            tools=OPENAI_TOOLS,
            tool_choice="auto",
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
                return envelope
            fallback = _fallback_envelope("validacion o transicion fallida")
            _force_fallback_state(db, user_id, fallback)
            return fallback

        # Solo hubo tools de datos: los resultados ya quedaron en el historial;
        # seguimos el loop para que el modelo decida el siguiente paso
        # (normalmente emit_screen).

    return ChatTextResponse(
        payload="Estoy teniendo problemas para armar esa pantalla, ¿puedes reformular tu pregunta?"
    )


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
