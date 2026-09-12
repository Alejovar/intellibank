from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.chat import ActionExecuteRequest, ChatResponse, SaveScreenRequest
from .. import auth as auth_module
from ..llm.orchestrator import run_action_result
from ..models import SavedScreen

router = APIRouter(prefix="/actions", tags=["actions"])


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
