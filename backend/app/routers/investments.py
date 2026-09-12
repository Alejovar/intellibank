"""Endpoints de consulta e historial del modulo de inversiones."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth as auth_module
from ..database import get_db
from ..llm.tools import (
    calculate_performance,
    get_investment_cashflows,
    get_investment_profile,
    get_portfolio,
)
from ..models import InterfaceHistory

router = APIRouter(prefix="/investments", tags=["investments"])


@router.get("/history")
def list_investment_history(
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    rows = (
        db.query(InterfaceHistory)
        .filter(InterfaceHistory.user_id == user.id)
        .order_by(InterfaceHistory.created_at.desc(), InterfaceHistory.id.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": row.id,
            "title": row.title,
            "prompt": row.user_prompt,
            "intent": row.intent,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "payload": {
                "mime_type": "application/a2ui+json",
                "payload": row.a2ui_payload,
            },
            "snapshot": row.data_snapshot or {},
        }
        for row in rows
    ]


@router.get("/history/{history_id}")
def get_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    row = (
        db.query(InterfaceHistory)
        .filter(InterfaceHistory.id == history_id, InterfaceHistory.user_id == user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Interfaz historica no encontrada")
    return {
        "id": row.id,
        "title": row.title,
        "prompt": row.user_prompt,
        "intent": row.intent,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "payload": {"mime_type": "application/a2ui+json", "payload": row.a2ui_payload},
        "snapshot": row.data_snapshot or {},
    }


@router.post("/history/{history_id}/replay")
def replay_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    """Reproduce una interfaz sin llamar al LLM.

    Solo se vuelven a ejecutar consultas de lectura conocidas. Las acciones de
    escritura nunca se repiten desde el historial.
    """
    row = (
        db.query(InterfaceHistory)
        .filter(InterfaceHistory.id == history_id, InterfaceHistory.user_id == user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Interfaz historica no encontrada")

    current = {
        "get_portfolio": get_portfolio(db, user.id),
        "calculate_performance": calculate_performance(db, user.id),
        "get_investment_cashflows": get_investment_cashflows(db, user.id),
        "get_investment_profile": get_investment_profile(db, user.id),
    }
    before = row.data_snapshot or {}
    before_portfolio = before.get("get_portfolio") or {}
    after_portfolio = current["get_portfolio"]

    return {
        "historyId": row.id,
        "title": row.title,
        "prompt": row.user_prompt,
        "originalPayload": {"mime_type": "application/a2ui+json", "payload": row.a2ui_payload},
        "before": before,
        "after": current,
        "comparison": {
            "beforeTotalValue": before_portfolio.get("totalValue"),
            "afterTotalValue": after_portfolio.get("totalValue"),
            "beforeTotalGain": before_portfolio.get("totalGain"),
            "afterTotalGain": after_portfolio.get("totalGain"),
        },
    }
