from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.chat import ChatMessageRequest, ChatResponse
from .. import auth as auth_module
from ..llm.orchestrator import run_turn

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
def send_message(
    body: ChatMessageRequest,
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    response = run_turn(
        db=db,
        user_id=user.id,
        user_full_name=user.full_name,
        active_categories=body.active_categories,
        user_message=body.message,
    )
    return ChatResponse(response=response)
