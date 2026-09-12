from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.chat import ActionExecuteRequest, ChatResponse, SaveScreenRequest
from .. import auth as auth_module
from ..llm.orchestrator import run_action_result
from ..models import SavedScreen, SessionState

router = APIRouter(prefix="/actions", tags=["actions"])

SENSITIVE_TOOLS = {
    "apply_credit_plan",
    "confirm_investment",
    "schedule_payment",
    "confirm_insurance_policy",
    "file_insurance_claim",
    "contribute_to_goal",
}


def _screen_actions(payload: dict | None) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    actions = list(payload.get("footer_actions") or [])
    for component in payload.get("components") or []:
        if isinstance(component, dict):
            actions.extend(component.get("actions") or [])
    return [action for action in actions if isinstance(action, dict)]


def _validate_action(db: Session, user_id: int, body: ActionExecuteRequest) -> None:
    state = db.get(SessionState, user_id)
    if state is None:
        raise HTTPException(
            status_code=409,
            detail="no hay una pantalla activa para ejecutar esta accion",
        )
    if body.screen_id != state.last_screen_id:
        raise HTTPException(status_code=409, detail="la pantalla ya no esta vigente")

    matches = [
        action
        for action in _screen_actions(state.last_screen_payload)
        if action.get("tool") == body.tool
    ]
    if not matches:
        raise HTTPException(
            status_code=403,
            detail="esa accion no esta disponible en la pantalla actual",
        )

    requires_confirmation = body.tool in SENSITIVE_TOOLS or any(
        action.get("requires_confirmation") or action.get("requires_biometric")
        for action in matches
    )
    pending = state.pending_action if isinstance(state.pending_action, dict) else {}
    pending_tools = pending.get("tools") or []
    confirmed = (
        state.current_stage == "confirmation"
        and pending.get("screen_id") == body.screen_id
        and body.tool in pending_tools
    )
    if requires_confirmation and not confirmed:
        raise HTTPException(
            status_code=403,
            detail="esta accion requiere pasar primero por una confirmacion",
        )


@router.post("/execute", response_model=ChatResponse)
def execute_action(
    body: ActionExecuteRequest,
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    """
    Punto de entrada UNICO para cualquier boton/slider/seleccion de una
    pantalla generada. Nunca se manda como un mensaje de chat nuevo: se
    ejecuta como tool call real contra el backend (regla #4 del hackathon).
    """
    _validate_action(db, user.id, body)
    response = run_action_result(
        db=db,
        user_id=user.id,
        user_full_name=user.full_name,
        active_categories=[],
        tool=body.tool,
        args=body.args,
    )
    return ChatResponse(response=response)


@router.post("/save-screen")
def save_screen(
    body: SaveScreenRequest,
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    saved = SavedScreen(user_id=user.id, title=body.title, a2ui_payload=body.a2ui_payload)
    db.add(saved)
    db.commit()
    return {"ok": True, "id": saved.id}


@router.get("/saved-screens")
def list_saved_screens(
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    rows = db.query(SavedScreen).filter(SavedScreen.user_id == user.id).all()
    return [{"id": r.id, "title": r.title, "payload": r.a2ui_payload} for r in rows]
