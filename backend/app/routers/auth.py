from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.chat import LoginRequest, LoginResponse
from .. import auth as auth_module
from ..llm.orchestrator import reset_history

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    token, user = auth_module.login(body.clave_bancaria, body.password, db)
    reset_history(db, user.id)
    return LoginResponse(
        token=token, full_name=user.full_name, onboarding_done=user.onboarding_done
    )


@router.post("/onboarding-complete")
def complete_onboarding(
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    user.onboarding_done = True
    db.commit()
    return {"ok": True}
