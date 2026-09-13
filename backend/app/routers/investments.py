"""Endpoints de consulta e historial del modulo de inversiones."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth as auth_module
from ..database import get_db
from ..llm.orchestrator import reset_history, run_turn
from ..models import InterfaceHistory
from ..schemas.chat import ChatResponse, HistoryReplayRequest

router = APIRouter(prefix="/investments", tags=["investments"])

REPLAY_READ_ONLY_TOOLS = {
    "get_credit_status",
    "get_restructure_options",
    "simulate_plan_payment",
    "get_investment_profile",
    "get_investment_products",
    "get_portfolio",
    "get_investment_cashflows",
    "calculate_performance",
    "compare_investments",
    "get_investment_history",
    "get_investment_options",
    "simulate_investment",
    "get_portfolio_overview",
    "get_fixed_income_products",
    "simulate_fixed_income",
    "get_investment_funds",
    "get_market_watchlist",
    "get_market_positions",
    "get_fx_rates",
    "quote_fx_exchange",
    "get_structured_notes",
    "get_insurance_products",
    "quote_insurance",
    "get_insurance_claims_info",
    "get_financial_diagnosis",
    "get_financial_goals",
    "get_habit_tips",
    "get_expenses_summary",
    "get_movements",
    "get_balance",
    "get_card_payment_info",
}


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


@router.post("/history/{history_id}/replay", response_model=ChatResponse)
def replay_history_item(
    history_id: int,
    body: HistoryReplayRequest,
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    """Vuelve a generar una interfaz histórica con datos actuales.

    La reproducción empieza con contexto conversacional limpio para que el LLM
    vuelva a invocar las funciones de dominio en lugar de contestar que ya
    mostró la pantalla. No se crea otra entrada duplicada en el historial.
    """
    row = (
        db.query(InterfaceHistory)
        .filter(InterfaceHistory.id == history_id, InterfaceHistory.user_id == user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Interfaz historica no encontrada")

    prompt = (row.user_prompt or "").strip()
    if not prompt:
        prompt = f"Genera nuevamente la interfaz: {row.title}"

    reset_history(db, user.id)
    response = run_turn(
        db=db,
        user_id=user.id,
        user_full_name=user.full_name,
        active_categories=body.active_categories,
        user_message=prompt,
        record_interface=False,
        allowed_domain_tools=REPLAY_READ_ONLY_TOOLS,
        require_interface=True,
    )
    return ChatResponse(response=response)
