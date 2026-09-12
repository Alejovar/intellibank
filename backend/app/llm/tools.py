"""
Tools de DOMINIO (logica de negocio determinista, en Python puro).
Estas son las funciones reales que:
  a) el LLM puede invocar durante su razonamiento para leer datos
     (ej. get_credit_status, get_expenses_summary), y
  b) el backend ejecuta directamente cuando el usuario hace click en
     un boton de una pantalla generada (accion -> tool -> resultado).

Ninguna de estas funciones genera UI. Solo leen/escriben SQLite y
regresan datos planos (dicts). El LLM decide despues como visualizarlos
con el catalogo de componentes.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import (
    Account, Movement, CreditAccount, ExpenseLimit, ScheduledPayment,
    InvestmentProfile, Investment, SharedExpenseGroup,
)


def _amortization_payment(principal: float, annual_rate_pct: float, months: int) -> float:
    r = (annual_rate_pct / 100) / 12
    if r == 0:
        return round(principal / months, 2)
    factor = (1 + r) ** months
    payment = principal * r * factor / (factor - 1)
    return round(payment, 2)


# ---------------------------------------------------------------- credito
def get_credit_status(db: Session, user_id: int) -> dict:
    c = db.query(CreditAccount).filter(CreditAccount.user_id == user_id).first()
    if not c:
        return {"error": "sin tarjeta de credito registrada"}
    return {
        "id": c.id, "label": c.label, "maskedNumber": c.masked_number,
        "balance": c.balance, "creditLimit": c.credit_limit,
        "available": round(c.credit_limit - c.balance, 2),
        "currentCat": c.current_cat,
        "activePlan": {
            "termMonths": c.plan_term_months,
            "monthlyPayment": c.plan_monthly_payment,
            "cat": c.plan_cat,
        } if c.plan_term_months else None,
    }


def get_restructure_options(db: Session, user_id: int, credit_account_id: int) -> dict:
    c = db.query(CreditAccount).get(credit_account_id)
    if not c or c.user_id != user_id:
        return {"error": "cuenta no encontrada"}
    plans = []
    # tasas ilustrativas: a mayor plazo, menor CAT y menor pago mensual
    plan_defs = [(12, 28.5), (18, 24.1), (24, 22.8)]
    for months, cat in plan_defs:
        payment = _amortization_payment(c.balance, cat, months)
        plans.append({
            "id": f"plan-{months}", "termMonths": months,
            "monthlyPayment": payment, "cat": cat,
        })
    return {"currentBalance": c.balance, "currentCat": c.current_cat, "plans": plans}


def simulate_plan_payment(db: Session, user_id: int, credit_account_id: int,
                           term_months: int) -> dict:
    """Recalcula pago mensual para un plazo arbitrario (usado por el slider)."""
    c = db.query(CreditAccount).get(credit_account_id)
    if not c or c.user_id != user_id:
        return {"error": "cuenta no encontrada"}
    # interpolamos un CAT ilustrativo entre 22% (36 meses) y 30% (6 meses)
    term_months = max(6, min(36, int(term_months)))
    cat = round(30 - (term_months - 6) * (30 - 22) / (36 - 6), 1)
    payment = _amortization_payment(c.balance, cat, term_months)
    curve = []
    for m in [6, 12, 18, 24, 30, 36]:
        m_cat = round(30 - (m - 6) * (30 - 22) / (36 - 6), 1)
        curve.append({"x": m, "y": _amortization_payment(c.balance, m_cat, m)})
    return {"termMonths": term_months, "cat": cat, "monthlyPayment": payment, "curve": curve}


def apply_credit_plan(db: Session, user_id: int, credit_account_id: int,
                       term_months: int, cat: float, monthly_payment: float) -> dict:
    c = db.query(CreditAccount).get(credit_account_id)
    if not c or c.user_id != user_id:
        return {"error": "cuenta no encontrada"}
    old_total_est = c.balance * (1 + c.current_cat / 100)
    new_total_est = monthly_payment * term_months
    c.plan_term_months = term_months
    c.plan_cat = cat
    c.plan_monthly_payment = monthly_payment
    db.commit()
    savings = round(max(old_total_est - new_total_est, 0), 2)
    return {
        "applied": True, "termMonths": term_months, "monthlyPayment": monthly_payment,
        "cat": cat, "estimatedSavings": savings,
    }


# ------------------------------------------------------------- inversiones
def set_investment_profile(db: Session, user_id: int, risk_profile: str) -> dict:
    p = db.query(InvestmentProfile).filter(InvestmentProfile.user_id == user_id).first()
    if not p:
        p = InvestmentProfile(user_id=user_id)
        db.add(p)
    p.risk_profile = risk_profile
    db.commit()
    return {"riskProfile": risk_profile}


_INVESTMENT_PRODUCTS = {
    "conservador": [
        {"id": "cetes", "title": "CETES", "rate": 9.8, "risk": "bajo"},
        {"id": "fondo_deuda", "title": "Fondo de deuda", "rate": 10.4, "risk": "bajo"},
    ],
    "moderado": [
        {"id": "fondo_deuda", "title": "Fondo de deuda", "rate": 10.4, "risk": "bajo"},
        {"id": "portafolio_balanceado", "title": "Portafolio balanceado", "rate": 12.1, "risk": "medio"},
    ],
    "dinamico": [
        {"id": "portafolio_balanceado", "title": "Portafolio balanceado", "rate": 12.1, "risk": "medio"},
        {"id": "portafolio_dinamico", "title": "Portafolio dinamico", "rate": 15.5, "risk": "alto"},
    ],
}


def get_investment_options(db: Session, user_id: int, amount: float,
                            risk_profile: str = "conservador") -> dict:
    products = _INVESTMENT_PRODUCTS.get(risk_profile, _INVESTMENT_PRODUCTS["conservador"])
    return {"amount": amount, "riskProfile": risk_profile, "products": products}


def simulate_investment(db: Session, user_id: int, product_id: str, amount: float,
                         term_months: int) -> dict:
    all_products = {p["id"]: p for lst in _INVESTMENT_PRODUCTS.values() for p in lst}
    product = all_products.get(product_id)
    if not product:
        return {"error": "producto no encontrado"}
    rate = product["rate"]
    monthly_rate = rate / 100 / 12
    curve = []
    value = amount
    for m in range(0, term_months + 1, max(1, term_months // 6)):
        value_at_m = amount * ((1 + monthly_rate) ** m)
        curve.append({"x": m, "y": round(value_at_m, 2)})
    final_value = round(amount * ((1 + monthly_rate) ** term_months), 2)
    return {
        "productId": product_id, "productTitle": product["title"], "rate": rate,
        "amount": amount, "termMonths": term_months, "finalValue": final_value,
        "gainPct": round((final_value / amount - 1) * 100, 1), "curve": curve,
    }


def confirm_investment(db: Session, user_id: int, product_id: str, product_title: str,
                        amount: float, term_months: int, rate: float) -> dict:
    inv = Investment(
        user_id=user_id, product=product_title, amount=amount,
        term_months=term_months, estimated_rate=rate, status="activo",
    )
    db.add(inv)
    db.commit()
    return {"confirmed": True, "investmentId": inv.id}


# --------------------------------------------------------- gastos y pagos
def get_expenses_summary(db: Session, user_id: int) -> dict:
    account = db.query(Account).filter(Account.user_id == user_id).first()
    movements = db.query(Movement).filter(
        Movement.account_id == account.id, Movement.amount < 0
    ).all()
    totals: dict[str, float] = {}
    for m in movements:
        totals[m.category] = totals.get(m.category, 0) + abs(m.amount)
    total = sum(totals.values()) or 1
    colors = {"Comida": "#EB0029", "Transporte": "#2E7BE5",
              "Entretenimiento": "#7B4FE0", "Otros": "#9AA0A6"}
    data = [
        {"label": cat, "value": round(v, 2), "pct": round(v / total * 100),
         "color": colors.get(cat, "#9AA0A6")}
        for cat, v in sorted(totals.items(), key=lambda x: -x[1])
    ]
    limit = db.query(ExpenseLimit).filter(
        ExpenseLimit.user_id == user_id, ExpenseLimit.category == "Comida"
    ).first()
    insight = None
    if limit:
        usage_pct = round(limit.current_usage / limit.monthly_limit * 100)
        insight = {
            "category": limit.category, "usage": limit.current_usage,
            "limit": limit.monthly_limit, "usagePct": usage_pct,
        }
    return {"total": round(total, 2), "byCategory": data, "limitInsight": insight}


def get_movements(db: Session, user_id: int, limit: int = 10) -> dict:
    account = db.query(Account).filter(Account.user_id == user_id).first()
    movs = (db.query(Movement).filter(Movement.account_id == account.id)
            .order_by(Movement.date.desc()).limit(limit).all())
    return {"movements": [
        {"date": m.date.strftime("%Y-%m-%d"), "description": m.description,
         "category": m.category, "amount": m.amount} for m in movs
    ]}


def get_balance(db: Session, user_id: int) -> dict:
    account = db.query(Account).filter(Account.user_id == user_id).first()
    return {
        "accountLabel": account.label, "maskedNumber": account.masked_number,
        "balance": account.balance, "currency": account.currency,
    }


def create_expense_limit(db: Session, user_id: int, category: str,
                          monthly_limit: float, alert_threshold_pct: int = 80) -> dict:
    existing = db.query(ExpenseLimit).filter(
        ExpenseLimit.user_id == user_id, ExpenseLimit.category == category
    ).first()
    if existing:
        existing.monthly_limit = monthly_limit
        existing.alert_threshold_pct = alert_threshold_pct
    else:
        existing = ExpenseLimit(
            user_id=user_id, category=category, monthly_limit=monthly_limit,
            alert_threshold_pct=alert_threshold_pct, current_usage=0.0,
        )
        db.add(existing)
    db.commit()
    return {"category": category, "monthlyLimit": monthly_limit,
            "alertThresholdPct": alert_threshold_pct}


def get_card_payment_info(db: Session, user_id: int) -> dict:
    c = db.query(CreditAccount).filter(CreditAccount.user_id == user_id).first()
    min_payment = round(c.balance * 0.045, 2)
    recommended = c.plan_monthly_payment or round(c.balance * 0.08, 2)
    due_date = (datetime.utcnow() + timedelta(days=16)).strftime("%Y-%m-%d")
    return {
        "cardLabel": c.label, "maskedNumber": c.masked_number,
        "minPayment": min_payment, "recommendedPayment": recommended,
        "dueDate": due_date,
    }


def schedule_payment(db: Session, user_id: int, amount: float, date: str) -> dict:
    c = db.query(CreditAccount).filter(CreditAccount.user_id == user_id).first()
    payment = ScheduledPayment(
        user_id=user_id, credit_account_id=c.id, amount=amount,
        scheduled_date=datetime.fromisoformat(date), status="programado",
    )
    db.add(payment)
    db.commit()
    return {"scheduled": True, "amount": amount, "date": date}


# --------------------------------------------------------- gasto compartido
def create_shared_expense_group(db: Session, user_id: int, title: str,
                                 people: list[str]) -> dict:
    group = SharedExpenseGroup(
        user_id=user_id, title=title,
        people=[{"name": p, "paid": 0.0, "owes": 0.0} for p in people],
        expenses=[],
    )
    db.add(group)
    db.commit()
    return {"groupId": group.id, "title": title, "people": group.people}


def add_shared_expense(db: Session, user_id: int, group_id: int, desc: str,
                        amount: float, paid_by: str) -> dict:
    group = db.query(SharedExpenseGroup).get(group_id)
    if not group or group.user_id != user_id:
        return {"error": "grupo no encontrado"}
    expenses = list(group.expenses or [])
    expenses.append({"desc": desc, "amount": amount, "paidBy": paid_by})
    people = list(group.people or [])
    n = len(people) or 1
    share = round(amount / n, 2)
    for person in people:
        if person["name"] == paid_by:
            person["paid"] += amount
        person["owes"] += share
    group.expenses = expenses
    group.people = people
    db.commit()
    return {"groupId": group.id, "people": people, "expenses": expenses}


# Registro de tools disponibles para el orquestador (nombre -> funcion)
TOOL_REGISTRY = {
    "get_credit_status": get_credit_status,
    "get_restructure_options": get_restructure_options,
    "simulate_plan_payment": simulate_plan_payment,
    "apply_credit_plan": apply_credit_plan,
    "set_investment_profile": set_investment_profile,
    "get_investment_options": get_investment_options,
    "simulate_investment": simulate_investment,
    "confirm_investment": confirm_investment,
    "get_expenses_summary": get_expenses_summary,
    "get_movements": get_movements,
    "get_balance": get_balance,
    "create_expense_limit": create_expense_limit,
    "get_card_payment_info": get_card_payment_info,
    "schedule_payment": schedule_payment,
    "create_shared_expense_group": create_shared_expense_group,
    "add_shared_expense": add_shared_expense,
}
