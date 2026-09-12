from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import auth as auth_module
from ..database import get_db
from ..llm.tools import (
    get_balance,
    get_credit_status,
    get_expenses_summary,
    get_movements,
)


router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/home-summary")
def home_summary(
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    """Datos deterministas para la pantalla fija de Inicio."""
    return {
        "user": {"fullName": user.full_name},
        "balance": get_balance(db, user.id),
        "creditStatus": get_credit_status(db, user.id),
        "recentMovements": get_movements(db, user.id, limit=4),
        "expensesSummary": get_expenses_summary(db, user.id),
    }
