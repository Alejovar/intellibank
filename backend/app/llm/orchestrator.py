"""
Orquestador de la conversacion: implementa el loop tool-use de Anthropic,
ejecuta las tools de dominio contra SQLite, y valida cualquier emision de
UI contra el esquema A2UI antes de dejarla salir hacia el frontend.

Este es el unico lugar del backend que "habla" con el LLM.
"""
from __future__ import annotations
import json
import logging
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .client import get_client, get_model
from .system_prompt import build_system_prompt
from .tool_specs import ALL_TOOLS
from .tools import TOOL_REGISTRY
from ..schemas.a2ui import A2UIScreen, A2UIClarification, A2UIEnvelope
from ..schemas.chat import ChatTextResponse

logger = logging.getLogger("banorte.orchestrator")

MAX_TOOL_ITERATIONS = 6

# Historial de conversacion en memoria, por usuario.
# En produccion: persistir en DB (ver models.ConversationTurn) o Redis.
_CONVERSATIONS: dict[int, list[dict]] = {}


def _history(user_id: int) -> list[dict]:
    return _CONVERSATIONS.setdefault(user_id, [])


def reset_history(user_id: int) -> None:
    _CONVERSATIONS[user_id] = []


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


def run_turn(
    db: Session,
    user_id: int,
    user_full_name: str,
    active_categories: list[str],
    user_message: str | None,
) -> ChatTextResponse | A2UIEnvelope:
    """Ejecuta un turno completo: agrega el mensaje del usuario (si hay),
    corre el loop de tool-use hasta que el LLM emita UI o texto plano."""
    history = _history(user_id)
    if user_message is not None:
        history.append({"role": "user", "content": user_message})

    system = build_system_prompt(active_categories, user_full_name)
    client = get_client()

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=get_model(),
            max_tokens=2000,
            system=system,
            messages=history,
            tools=ALL_TOOLS,
        )

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        # Guardamos la respuesta del asistente tal cual (puede tener texto + tool_use)
        history.append({"role": "assistant", "content": response.content})

        if not tool_use_blocks:
            # Respuesta en texto plano (p.ej. fuera de dominio, o charla simple)
            text = "\n".join(b.text for b in text_blocks).strip() or "¿En que mas te puedo ayudar?"
            return ChatTextResponse(payload=text)

        # Puede haber una tool de UI y/o varias tools de datos en la misma vuelta.
        ui_block = next((b for b in tool_use_blocks if b.name in ("emit_screen", "emit_clarification")), None)
        domain_blocks = [b for b in tool_use_blocks if b.name not in ("emit_screen", "emit_clarification")]

        tool_results_content = []

        for block in domain_blocks:
            result = _run_domain_tool(db, user_id, block.name, block.input)
            tool_results_content.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        if ui_block:
            envelope = _build_ui_response(ui_block.name, ui_block.input)
            # Cerramos el tool_use con un ack para mantener el historial valido
            tool_results_content.append({
                "type": "tool_result",
                "tool_use_id": ui_block.id,
                "content": json.dumps({"delivered": envelope is not None}),
            })
            history.append({"role": "user", "content": tool_results_content})
            return envelope or _fallback_envelope("validacion fallida")

        # Solo hubo tools de datos: agregamos resultados y seguimos el loop
        # para que el modelo decida el siguiente paso (normalmente emit_screen).
        history.append({"role": "user", "content": tool_results_content})

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
