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
    InvestmentProfile, Investment, InsurancePolicy, InsuranceClaim,
    FinancialGoal, SharedExpenseGroup, InvestmentProduct, InvestmentTransaction,
    PortfolioSnapshot, InterfaceHistory,
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


def get_investment_profile(db: Session, user_id: int) -> dict:
    profile = (
        db.query(InvestmentProfile)
        .filter(InvestmentProfile.user_id == user_id)
        .first()
    )
    return {"riskProfile": profile.risk_profile if profile else None}


def get_investment_products(
    db: Session, user_id: int, risk_profile: str | None = None
) -> dict:
    """Lista el catalogo persistido; usa el catalogo base como fallback."""
    profile = risk_profile or get_investment_profile(db, user_id).get("riskProfile")
    products = db.query(InvestmentProduct).filter(InvestmentProduct.active.is_(True)).all()
    if products:
        rows = [
            {
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "risk": product.risk_level,
                "rate": product.annual_rate,
                "minAmount": product.min_amount,
            }
            for product in products
        ]
    else:
        rows = [dict(product) for group in _INVESTMENT_PRODUCTS.values() for product in group]
    if profile in _INVESTMENT_PRODUCTS:
        allowed = {product["id"] for product in _INVESTMENT_PRODUCTS[profile]}
        rows = [product for product in rows if product["id"] in allowed]
    return {"riskProfile": profile, "products": rows}


def _portfolio_rows(db: Session, user_id: int) -> list[dict]:
    positions = (
        db.query(Investment)
        .filter(Investment.user_id == user_id, Investment.status == "activo")
        .order_by(Investment.opened_at, Investment.id)
        .all()
    )
    rows = []
    for position in positions:
        invested = round(position.amount or 0.0, 2)
        current = round(
            position.current_value if position.current_value is not None else invested, 2
        )
        gain = round(current - invested, 2)
        rows.append({
            "id": position.id,
            "productId": position.product_id,
            "product": position.product,
            "amount": invested,
            "currentValue": current,
            "gain": gain,
            "gainPct": round((gain / invested) * 100, 2) if invested else 0.0,
            "termMonths": position.term_months,
            "rate": position.estimated_rate,
            "status": position.status,
            "openedAt": position.opened_at.isoformat() if position.opened_at else None,
        })
    return rows


def _capture_portfolio_snapshot(db: Session, user_id: int) -> PortfolioSnapshot:
    rows = _portfolio_rows(db, user_id)
    total_invested = round(sum(row["amount"] for row in rows), 2)
    total_value = round(sum(row["currentValue"] for row in rows), 2)
    snapshot = PortfolioSnapshot(
        user_id=user_id,
        total_invested=total_invested,
        total_value=total_value,
        total_gain=round(total_value - total_invested, 2),
        positions=rows,
    )
    db.add(snapshot)
    return snapshot


def get_portfolio(db: Session, user_id: int) -> dict:
    """Resumen de posiciones con costo base, valor actual y ganancia/perdida."""
    rows = _portfolio_rows(db, user_id)
    total_invested = round(sum(row["amount"] for row in rows), 2)
    total_value = round(sum(row["currentValue"] for row in rows), 2)
    total_gain = round(total_value - total_invested, 2)
    return {
        "totalInvested": total_invested,
        "totalValue": total_value,
        "totalGain": total_gain,
        "gainPct": round((total_gain / total_invested) * 100, 2) if total_invested else 0.0,
        "positions": rows,
        "isEmpty": not rows,
    }


def get_investment_cashflows(
    db: Session, user_id: int, limit: int = 20
) -> dict:
    """Devuelve aportaciones, retiros, ganancias y cargos del portafolio."""
    transactions = (
        db.query(InvestmentTransaction)
        .filter(InvestmentTransaction.user_id == user_id)
        .order_by(
            InvestmentTransaction.occurred_at.desc(),
            InvestmentTransaction.id.desc(),
        )
        .limit(max(1, min(limit, 100)))
        .all()
    )
    rows = [
        {
            "id": row.id,
            "type": row.transaction_type,
            "amount": round(row.amount, 2),
            "description": row.description or row.transaction_type.title(),
            "date": row.occurred_at.isoformat() if row.occurred_at else None,
        }
        for row in transactions
    ]
    return {
        "transactions": rows,
        "totalDeposits": round(sum(row["amount"] for row in rows if row["type"] == "deposit"), 2),
        "totalWithdrawals": round(sum(abs(row["amount"]) for row in rows if row["type"] == "withdrawal"), 2),
        "totalGains": round(sum(row["amount"] for row in rows if row["type"] == "gain"), 2),
    }


def calculate_performance(db: Session, user_id: int) -> dict:
    """Calcula rendimiento agregado y por posicion de forma determinista."""
    portfolio = get_portfolio(db, user_id)
    points = [
        {
            "label": row["product"],
            "value": row["gain"],
            "returnPct": row["gainPct"],
        }
        for row in portfolio["positions"]
    ]
    return {
        "totalInvested": portfolio["totalInvested"],
        "currentValue": portfolio["totalValue"],
        "totalGain": portfolio["totalGain"],
        "returnPct": portfolio["gainPct"],
        "byPosition": points,
        "trend": "positive" if portfolio["totalGain"] >= 0 else "negative",
    }


def compare_investments(
    db: Session,
    user_id: int,
    product_ids: list[str],
    amount: float,
    term_months: int,
) -> dict:
    """Compara hasta cuatro productos con el mismo monto y plazo."""
    all_products = {p["id"]: p for group in _INVESTMENT_PRODUCTS.values() for p in group}
    catalog_products = db.query(InvestmentProduct).filter(InvestmentProduct.active.is_(True)).all()
    all_products.update({
        product.id: {
            "id": product.id,
            "title": product.title,
            "rate": product.annual_rate,
            "risk": product.risk_level,
        }
        for product in catalog_products
    })
    selected = []
    for product_id in product_ids[:4]:
        product = all_products.get(product_id)
        if not product:
            continue
        monthly_rate = product["rate"] / 100 / 12
        final_value = round(amount * ((1 + monthly_rate) ** term_months), 2)
        selected.append({
            "productId": product_id,
            "title": product["title"],
            "risk": product["risk"],
            "rate": product["rate"],
            "amount": amount,
            "termMonths": term_months,
            "finalValue": final_value,
            "estimatedGain": round(final_value - amount, 2),
        })
    return {"amount": amount, "termMonths": term_months, "products": selected}


def get_investment_history(db: Session, user_id: int, limit: int = 20) -> dict:
    """Lista resumida de interfaces generadas, apta para renderizar en chat."""
    rows = (
        db.query(InterfaceHistory)
        .filter(InterfaceHistory.user_id == user_id)
        .order_by(InterfaceHistory.created_at.desc(), InterfaceHistory.id.desc())
        .limit(max(1, min(limit, 100)))
        .all()
    )
    return {"options": [
        {
            "id": str(row.id),
            "title": row.title,
            "intent": row.intent,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "subtitle": row.intent,
            "badge": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]}

_FIXED_INCOME_PRODUCTS = {
    "renta_fija": [
        {"id": "pagare_28", "title": "Pagare Banorte 28 dias", "issuer": "Banorte", "termMonths": 1, "rate": 9.1},
        {"id": "pagare_90", "title": "Pagare Banorte 90 dias", "issuer": "Banorte", "termMonths": 3, "rate": 9.5},
        {"id": "cede_180", "title": "CEDE Banorte 180 dias", "issuer": "Banorte", "termMonths": 6, "rate": 9.9},
    ],
    "deuda": [
        {"id": "cetes_28", "title": "CETES 28 dias", "issuer": "Gobierno de Mexico", "termMonths": 1, "rate": 9.3},
        {"id": "cetes_182", "title": "CETES 182 dias", "issuer": "Gobierno de Mexico", "termMonths": 6, "rate": 9.7},
        {"id": "bono_m_36", "title": "Bono M 3 anos", "issuer": "Gobierno de Mexico", "termMonths": 36, "rate": 10.1},
    ],
}

_INVESTMENT_FUNDS = [
    {"id": "fondo_acciones_mexico", "title": "Fondo Acciones Mexico", "category": "renta_variable", "historicalAnnualReturn": 14.2, "riskLevel": "alto", "minimumInvestment": 5000.0, "description": "Canasta diversificada de empresas mexicanas."},
    {"id": "fondo_acciones_global", "title": "Fondo Acciones Global", "category": "renta_variable", "historicalAnnualReturn": 15.8, "riskLevel": "alto", "minimumInvestment": 10000.0, "description": "Exposicion diversificada a mercados internacionales."},
    {"id": "fondo_deuda_corto", "title": "Fondo Deuda Corto Plazo", "category": "renta_fija", "historicalAnnualReturn": 9.6, "riskLevel": "bajo", "minimumInvestment": 1000.0, "description": "Instrumentos de deuda de corta duracion."},
    {"id": "fondo_balanceado", "title": "Fondo Balanceado Plus", "category": "balanceado", "historicalAnnualReturn": 12.4, "riskLevel": "medio", "minimumInvestment": 5000.0, "description": "Mezcla de deuda y renta variable para diversificar."},
]

_STRUCTURED_NOTES = [
    {"id": "nota_sp500_12", "title": "Nota Protegida S&P 500", "underlying": "S&P 500", "capitalProtectionPct": 90.0, "potentialReturnMin": 6.0, "potentialReturnMax": 14.0, "termMonths": 12},
    {"id": "nota_ipc_18", "title": "Nota Digital IPC", "underlying": "S&P/BMV IPC", "capitalProtectionPct": 85.0, "potentialReturnMin": 7.0, "potentialReturnMax": 16.0, "termMonths": 18},
    {"id": "nota_usdmxn_6", "title": "Nota Rango USD/MXN", "underlying": "USD/MXN", "capitalProtectionPct": 100.0, "potentialReturnMin": 5.0, "potentialReturnMax": 10.5, "termMonths": 6},
]

_MARKET_WATCHLIST = [
    {"symbol": "NAFTRAC.MX", "name": "ETF indice mexicano", "price": 58.42, "changePct": 0.64, "currency": "MXN"},
    {"symbol": "FEMSAUBD.MX", "name": "FEMSA", "price": 198.35, "changePct": -0.41, "currency": "MXN"},
    {"symbol": "IVV", "name": "iShares Core S&P 500 ETF", "price": 592.18, "changePct": 0.82, "currency": "USD"},
    {"symbol": "AAPL", "name": "Apple Inc.", "price": 226.74, "changePct": -0.18, "currency": "USD"},
]

_FX_RATES = [
    {"symbol": "USD/MXN", "name": "Dolar estadounidense / Peso mexicano", "price": 19.86, "rate": 19.86, "changePct": 0.22, "currency": "MXN"},
    {"symbol": "EUR/MXN", "name": "Euro / Peso mexicano", "price": 21.74, "rate": 21.74, "changePct": -0.16, "currency": "MXN"},
    {"symbol": "USD/EUR", "name": "Dolar estadounidense / Euro", "price": 0.9135, "rate": 0.9135, "changePct": 0.08, "currency": "EUR"},
]


def get_investment_options(db: Session, user_id: int, amount: float,
                            risk_profile: str = "conservador") -> dict:
    products = _INVESTMENT_PRODUCTS.get(risk_profile, _INVESTMENT_PRODUCTS["conservador"])
    return {"amount": amount, "riskProfile": risk_profile, "products": products}


def simulate_investment(db: Session, user_id: int, product_id: str, amount: float,
                         term_months: int) -> dict:
    all_products = {p["id"]: p for lst in _INVESTMENT_PRODUCTS.values() for p in lst}
    all_products.update({
        p["id"]: {"id": p["id"], "title": p["title"], "rate": p["historicalAnnualReturn"]}
        for p in _INVESTMENT_FUNDS
    })
    all_products.update({
        p["id"]: {"id": p["id"], "title": p["title"], "rate": p["potentialReturnMax"]}
        for p in _STRUCTURED_NOTES
    })
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
                        amount: float, term_months: int, rate: float,
                        category: str = "general", details: dict | None = None) -> dict:
    inv = Investment(
        user_id=user_id, product=product_title, amount=amount,
        term_months=term_months, estimated_rate=rate, status="activo",
        category=category, details=details,
    )
    db.add(inv)
    db.commit()
    return {"confirmed": True, "investmentId": inv.id}


def get_portfolio_overview(db: Session, user_id: int) -> dict:
    account = db.query(Account).filter(Account.user_id == user_id).first()
    investments = db.query(Investment).filter(Investment.user_id == user_id).all()
    subtotals: dict[str, float] = {}
    for investment in investments:
        category = investment.category or "general"
        subtotals[category] = subtotals.get(category, 0.0) + (investment.amount or 0.0)
    invested_total = round(sum(subtotals.values()), 2)
    cash = round(account.balance, 2) if account else 0.0
    portfolio_total = round(cash + invested_total, 2)
    colors = ["#C2002E", "#2D6FE0", "#8B5CF6", "#2E8B57", "#D97706", "#64748B", "#DB2777", "#0891B2"]
    chart_data = []
    for index, (category, subtotal) in enumerate(sorted(subtotals.items())):
        chart_data.append({
            "label": category.replace("_", " ").title(), "value": round(subtotal, 2),
            "pct": round(subtotal / invested_total * 100, 1) if invested_total else 0.0,
            "color": colors[index % len(colors)], "category": category,
        })
    return {
        "accountLabel": account.label if account else "Cuenta principal",
        "maskedNumber": account.masked_number if account else "",
        "currency": account.currency if account else "MXN", "cashBalance": cash,
        "investedTotal": invested_total, "portfolioTotal": portfolio_total,
        "investmentCount": len(investments), "categories": chart_data,
        "chartData": chart_data,
    }


def get_fixed_income_products(db: Session, user_id: int, category: str) -> dict:
    products = _FIXED_INCOME_PRODUCTS.get(category)
    if products is None:
        return {"error": "categoria invalida; usa renta_fija o deuda"}
    return {"category": category, "products": [{
        **product,
        "subtitle": f'{product["issuer"]} · {product["termMonths"]} meses',
        "badge": f'{product["rate"]}% anual',
    } for product in products]}


def simulate_fixed_income(db: Session, user_id: int, product_id: str,
                          category: str, amount: float, term_months: int) -> dict:
    products = _FIXED_INCOME_PRODUCTS.get(category)
    if products is None:
        return {"error": "categoria invalida; usa renta_fija o deuda"}
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return {"error": "producto no encontrado"}
    if amount <= 0 or term_months <= 0:
        return {"error": "monto y plazo deben ser mayores a cero"}
    monthly_rate = product["rate"] / 100 / 12
    curve = []
    for month in range(0, term_months + 1, max(1, term_months // 6)):
        curve.append({"x": month, "y": round(amount * ((1 + monthly_rate) ** month), 2)})
    final_value = round(amount * ((1 + monthly_rate) ** term_months), 2)
    return {
        "productId": product_id, "productTitle": product["title"], "category": category,
        "rate": product["rate"], "amount": amount, "termMonths": term_months,
        "finalValue": final_value, "gainPct": round((final_value / amount - 1) * 100, 1),
        "curve": curve,
    }


def get_investment_funds(db: Session, user_id: int, category: str | None = None) -> dict:
    allowed = {"renta_variable", "renta_fija", "balanceado"}
    if category is not None and category not in allowed:
        return {"error": "categoria de fondo invalida"}
    funds = [fund for fund in _INVESTMENT_FUNDS if category is None or fund["category"] == category]
    return {"category": category, "funds": [{
        **fund,
        "subtitle": f'{fund["description"]} Minimo ${fund["minimumInvestment"]:,.0f} MXN',
        "badge": f'{fund["historicalAnnualReturn"]}% hist. · riesgo {fund["riskLevel"]}',
    } for fund in funds]}


def get_market_watchlist(db: Session, user_id: int) -> dict:
    return {"title": "Mercado demo", "items": [dict(item) for item in _MARKET_WATCHLIST],
            "asOf": "Datos sinteticos para demostracion"}


def buy_market_position(db: Session, user_id: int, symbol: str,
                        quantity: float, price: float) -> dict:
    if quantity <= 0 or price <= 0:
        return {"error": "cantidad y precio deben ser mayores a cero"}
    market_item = next((item for item in _MARKET_WATCHLIST if item["symbol"].upper() == symbol.upper()), None)
    normalized_symbol = market_item["symbol"] if market_item else symbol.upper()
    amount = round(quantity * price, 2)
    inv = Investment(
        user_id=user_id, product=normalized_symbol, amount=amount, term_months=None,
        estimated_rate=None, status="activo", category="mercado",
        details={"symbol": normalized_symbol, "quantity": quantity, "price": price},
    )
    db.add(inv)
    db.commit()
    return {
        "confirmed": True, "investmentId": inv.id, "symbol": normalized_symbol,
        "quantity": quantity, "price": price, "amount": amount,
    }


def get_market_positions(db: Session, user_id: int) -> dict:
    prices = {item["symbol"]: item for item in _MARKET_WATCHLIST}
    investments = db.query(Investment).filter(
        Investment.user_id == user_id, Investment.category == "mercado"
    ).order_by(Investment.id).all()
    positions = []
    for investment in investments:
        details = investment.details or {}
        symbol = details.get("symbol", investment.product)
        quantity = details.get("quantity", 0)
        purchase_price = details.get("price", 0)
        current_price = prices.get(symbol, {}).get("price", purchase_price)
        current_value = round(quantity * current_price, 2)
        gain_loss = round(current_value - (investment.amount or 0), 2)
        positions.append({
            "id": investment.id, "symbol": symbol,
            "name": prices.get(symbol, {}).get("name", investment.product),
            "quantity": quantity, "purchasePrice": purchase_price,
            "currentPrice": current_price, "currentValue": current_value,
            "gainLoss": gain_loss, "currency": prices.get(symbol, {}).get("currency"),
            "title": symbol, "subtitle": f'{quantity:g} titulos · valor ${current_value:,.2f}',
            "badge": f'{gain_loss:+,.2f}',
        })
    return {"positions": positions, "totalCurrentValue": round(sum(p["currentValue"] for p in positions), 2)}


def get_fx_rates(db: Session, user_id: int) -> dict:
    return {"title": "Tipos de cambio demo", "items": [dict(item) for item in _FX_RATES],
            "asOf": "Datos sinteticos para demostracion"}


def quote_fx_exchange(db: Session, user_id: int, from_currency: str,
                      to_currency: str, amount: float) -> dict:
    if amount <= 0:
        return {"error": "el monto debe ser mayor a cero"}
    from_code, to_code = from_currency.upper(), to_currency.upper()
    direct = next((item for item in _FX_RATES if item["symbol"] == f"{from_code}/{to_code}"), None)
    inverse = next((item for item in _FX_RATES if item["symbol"] == f"{to_code}/{from_code}"), None)
    if direct:
        rate = direct["rate"]
    elif inverse:
        rate = 1 / inverse["rate"]
    else:
        return {"error": "par de divisas no disponible"}
    converted = round(amount * rate, 2)
    return {
        "fromCurrency": from_code, "toCurrency": to_code, "amount": amount,
        "rate": round(rate, 6), "convertedAmount": converted,
        "note": "Tipo de cambio sintetico para demostracion; no es una cotizacion en tiempo real.",
    }


def confirm_fx_exchange(db: Session, user_id: int, from_currency: str,
                        to_currency: str, amount: float, rate: float,
                        converted_amount: float) -> dict:
    if amount <= 0 or rate <= 0 or converted_amount <= 0:
        return {"error": "monto, tasa y monto convertido deben ser mayores a cero"}
    from_code, to_code = from_currency.upper(), to_currency.upper()
    details = {"fromCurrency": from_code, "toCurrency": to_code,
               "rate": rate, "convertedAmount": converted_amount}
    inv = Investment(
        user_id=user_id, product=f"{from_code}/{to_code}", amount=amount,
        term_months=None, estimated_rate=None, status="activo", category="divisas",
        details=details,
    )
    db.add(inv)
    db.commit()
    return {"confirmed": True, "investmentId": inv.id, **details, "amount": amount}


def get_structured_notes(db: Session, user_id: int) -> dict:
    return {"notes": [{
        **note,
        "subtitle": f'{note["underlying"]} · {note["termMonths"]} meses · proteccion {note["capitalProtectionPct"]}%',
        "badge": f'{note["potentialReturnMin"]}-{note["potentialReturnMax"]}% potencial',
    } for note in _STRUCTURED_NOTES]}


# ---------------------------------------------------------------- seguros
_INSURANCE_PRODUCTS = {
    "auto": {
        "id": "auto", "title": "Seguro de auto", "monthlyPremium": 620.0,
        "coverageSummary": "Danos a terceros, robo total y asistencia vial",
        "deductible": "5% danos materiales / 10% robo total", "icon": "auto",
    },
    "vida": {
        "id": "vida", "title": "Seguro de vida", "monthlyPremium": 390.0,
        "coverageSummary": "Proteccion por fallecimiento e invalidez total",
        "deductible": "Sin deducible", "icon": "vida",
    },
    "hogar": {
        "id": "hogar", "title": "Seguro de hogar", "monthlyPremium": 470.0,
        "coverageSummary": "Incendio, robo y danos por agua",
        "deductible": "$3,000 MXN por evento", "icon": "hogar",
    },
}

_COVERAGE_FACTORS = {"basica": 0.8, "amplia": 1.0, "premium": 1.35}


def get_insurance_products(db: Session, user_id: int) -> dict:
    products = []
    for product in _INSURANCE_PRODUCTS.values():
        products.append({
            **product,
            "subtitle": product["coverageSummary"],
            "badge": f'Desde ${product["monthlyPremium"]:,.2f}/mes',
        })
    return {"products": products}


def quote_insurance(db: Session, user_id: int, product_id: str,
                    coverage_level: str) -> dict:
    product = _INSURANCE_PRODUCTS.get(product_id)
    factor = _COVERAGE_FACTORS.get(coverage_level)
    if not product:
        return {"error": "producto de seguro no encontrado"}
    if factor is None:
        return {"error": "nivel de cobertura no valido"}
    monthly_premium = round(product["monthlyPremium"] * factor, 2)
    annual_premium = round(monthly_premium * 12, 2)
    return {
        "productId": product_id, "productTitle": product["title"],
        "coverageLevel": coverage_level, "monthlyPremium": monthly_premium,
        "annualPremium": annual_premium,
        "coverageSummary": product["coverageSummary"],
        "deductible": product["deductible"],
    }


def confirm_insurance_policy(db: Session, user_id: int, product_id: str,
                             product_title: str, monthly_premium: float,
                             coverage_level: str) -> dict:
    if product_id not in _INSURANCE_PRODUCTS:
        return {"error": "producto de seguro no encontrado"}
    if coverage_level not in _COVERAGE_FACTORS:
        return {"error": "nivel de cobertura no valido"}
    if monthly_premium <= 0:
        return {"error": "la prima mensual debe ser mayor a cero"}
    policy = InsurancePolicy(
        user_id=user_id, product=product_title, coverage_level=coverage_level,
        monthly_premium=round(monthly_premium, 2), status="activa",
    )
    db.add(policy)
    db.commit()
    return {
        "confirmed": True, "policyId": policy.id, "status": policy.status,
        "title": "Poliza contratada",
        "message": f"Tu {product_title} ya esta activo.",
        "details": [
            {"label": "Cobertura", "value": coverage_level},
            {"label": "Prima mensual", "value": f"${policy.monthly_premium:,.2f} MXN"},
            {"label": "Folio", "value": f"POL-{policy.id:06d}"},
        ],
    }


def get_insurance_claims_info(db: Session, user_id: int) -> dict:
    policies = db.query(InsurancePolicy).filter(
        InsurancePolicy.user_id == user_id, InsurancePolicy.status == "activa"
    ).order_by(InsurancePolicy.id).all()
    return {
        "hasActivePolicy": bool(policies),
        "activePolicies": [
            {
                "id": p.id, "title": p.product,
                "subtitle": f"Cobertura {p.coverage_level}",
                "badge": f"POL-{p.id:06d}",
            }
            for p in policies
        ],
        "steps": [
            "Protege a las personas y evita agravar el dano.",
            "Documenta el incidente con fotos y una descripcion breve.",
            "Reporta el siniestro y conserva tu numero de folio.",
        ],
        "requiredDocuments": ["Identificacion oficial", "Poliza", "Evidencia del incidente"],
        "claimsPhone": "800-555-0101",
        "claimsPortal": "portal.demo/seguros/siniestros",
    }


def file_insurance_claim(db: Session, user_id: int, policy_id: int,
                         description: str) -> dict:
    policy = db.query(InsurancePolicy).get(policy_id)
    if not policy or policy.user_id != user_id or policy.status != "activa":
        return {"error": "poliza activa no encontrada"}
    if not description.strip():
        return {"error": "la descripcion del siniestro es obligatoria"}
    claim = InsuranceClaim(
        policy_id=policy.id, user_id=user_id, description=description.strip(),
        status="en revision",
    )
    db.add(claim)
    db.commit()
    return {
        "filed": True, "claimId": claim.id, "policyId": policy.id,
        "status": claim.status, "title": "Siniestro reportado",
        "message": "Recibimos tu reporte y un ajustador dara seguimiento.",
        "details": [
            {"label": "Folio", "value": f"SIN-{claim.id:06d}"},
            {"label": "Poliza", "value": f"POL-{policy.id:06d}"},
            {"label": "Estado", "value": claim.status},
        ],
    }


# ------------------------------------------------ educacion financiera
def get_financial_diagnosis(db: Session, user_id: int) -> dict:
    account = db.query(Account).filter(Account.user_id == user_id).first()
    movements = []
    if account:
        movements = db.query(Movement).filter(Movement.account_id == account.id).all()
    income = round(sum(m.amount for m in movements if m.amount > 0), 2)
    expenses = round(sum(abs(m.amount) for m in movements if m.amount < 0), 2)
    savings = round(max(income - expenses, 0), 2)
    savings_rate = round((income - expenses) / income * 100, 1) if income else 0.0
    credit = db.query(CreditAccount).filter(CreditAccount.user_id == user_id).first()
    credit_utilization = round(credit.balance / credit.credit_limit * 100, 1) \
        if credit and credit.credit_limit else 0.0
    savings_points = max(0.0, min(50.0, savings_rate * 2.5))
    credit_points = max(0.0, min(30.0, 30.0 - credit_utilization * 0.3))
    liquidity_points = 20.0 if account and account.balance >= expenses else 10.0
    score = round(max(0.0, min(100.0, savings_points + credit_points + liquidity_points)))
    level = "saludable" if score >= 75 else "estable" if score >= 50 else "por mejorar"
    if savings_rate < 10:
        insight = "Tu principal oportunidad es separar al menos 10% de tus ingresos para ahorro."
    elif credit_utilization > 30:
        insight = "Reducir el uso de tu linea de credito puede fortalecer tu salud financiera."
    else:
        insight = "Mantienes un buen balance entre ahorro, gasto y uso de credito."
    total_flow = income + expenses or 1
    return {
        "score": score, "level": level, "insight": insight,
        "monthlyIncome": income, "monthlyExpenses": expenses,
        "estimatedSavings": savings, "savingsRate": savings_rate,
        "creditUtilization": credit_utilization,
        "availableBalance": round(account.balance, 2) if account else 0.0,
        "chartData": [
            {"label": "Ingresos", "value": income,
             "pct": round(income / total_flow * 100), "color": "#2E7BE5"},
            {"label": "Gastos", "value": expenses,
             "pct": round(expenses / total_flow * 100), "color": "#EB0029"},
        ],
    }


def set_financial_goal(db: Session, user_id: int, goal_name: str,
                       target_amount: float, target_date: str,
                       term: str | None = None) -> dict:
    if target_amount <= 0:
        return {"error": "la meta debe ser mayor a cero"}
    try:
        parsed_date = datetime.fromisoformat(target_date)
    except ValueError:
        return {"error": "fecha objetivo invalida; usa YYYY-MM-DD"}
    goal = FinancialGoal(
        user_id=user_id, name=goal_name, target_amount=round(target_amount, 2),
        target_date=parsed_date, saved_amount=0.0, term=term,
    )
    db.add(goal)
    db.commit()
    return {
        "goalId": goal.id, "name": goal.name, "targetAmount": goal.target_amount,
        "targetDate": goal.target_date.strftime("%Y-%m-%d"),
        "savedAmount": goal.saved_amount, "progressPercent": 0.0, "term": goal.term,
    }


def get_financial_goals(db: Session, user_id: int) -> dict:
    goals = db.query(FinancialGoal).filter(
        FinancialGoal.user_id == user_id
    ).order_by(FinancialGoal.id).all()
    return {"goals": [
        {
            "id": goal.id, "title": goal.name,
            "subtitle": f'${goal.saved_amount:,.2f} de ${goal.target_amount:,.2f} MXN',
            "badge": f'{round(goal.saved_amount / goal.target_amount * 100)}%',
            "targetAmount": goal.target_amount, "savedAmount": goal.saved_amount,
            "targetDate": goal.target_date.strftime("%Y-%m-%d"),
            "progressPercent": round(goal.saved_amount / goal.target_amount * 100, 1),
            "term": goal.term,
        }
        for goal in goals
    ]}


def contribute_to_goal(db: Session, user_id: int, goal_id: int, amount: float) -> dict:
    goal = db.query(FinancialGoal).get(goal_id)
    if not goal or goal.user_id != user_id:
        return {"error": "meta financiera no encontrada"}
    if amount <= 0:
        return {"error": "la aportacion debe ser mayor a cero"}
    previous_amount = goal.saved_amount or 0.0
    goal.saved_amount = round(min(previous_amount + amount, goal.target_amount), 2)
    applied_amount = round(goal.saved_amount - previous_amount, 2)
    db.commit()
    progress = round(goal.saved_amount / goal.target_amount * 100, 1)
    return {
        "contributed": True, "goalId": goal.id, "name": goal.name,
        "appliedAmount": applied_amount, "savedAmount": goal.saved_amount,
        "targetAmount": goal.target_amount, "progressPercent": progress,
        "completed": goal.saved_amount >= goal.target_amount,
    }


def get_habit_tips(db: Session, user_id: int, focus_area: str) -> dict:
    tips_by_area = {
        "ahorro": [
            "Aparta una cantidad fija el dia que recibes ingresos.",
            "Crea una meta con monto y fecha para dar seguimiento semanal.",
            "Conserva un fondo separado para evitar usarlo en gastos cotidianos.",
        ],
        "gasto": [
            "Define un limite semanal para tus categorias variables.",
            "Revisa tus movimientos dos veces por semana.",
            "Espera 24 horas antes de una compra no planeada.",
        ],
        "deuda": [
            "Prioriza la deuda con mayor tasa de interes.",
            "Paga mas que el minimo siempre que tu presupuesto lo permita.",
            "Evita nuevas compras a credito mientras reduces el saldo.",
        ],
    }
    tips = tips_by_area.get(focus_area)
    if tips is None:
        return {"error": "area de enfoque no valida"}
    return {
        "focusArea": focus_area, "title": f"Habitos para {focus_area}",
        "tips": tips, "text": " ".join(f"{i + 1}. {tip}" for i, tip in enumerate(tips)),
    }


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
    "get_investment_profile": get_investment_profile,
    "get_investment_products": get_investment_products,
    "get_portfolio": get_portfolio,
    "get_investment_cashflows": get_investment_cashflows,
    "calculate_performance": calculate_performance,
    "compare_investments": compare_investments,
    "get_investment_history": get_investment_history,
    "get_investment_options": get_investment_options,
    "simulate_investment": simulate_investment,
    "confirm_investment": confirm_investment,
    "get_portfolio_overview": get_portfolio_overview,
    "get_fixed_income_products": get_fixed_income_products,
    "simulate_fixed_income": simulate_fixed_income,
    "get_investment_funds": get_investment_funds,
    "get_market_watchlist": get_market_watchlist,
    "buy_market_position": buy_market_position,
    "get_market_positions": get_market_positions,
    "get_fx_rates": get_fx_rates,
    "quote_fx_exchange": quote_fx_exchange,
    "confirm_fx_exchange": confirm_fx_exchange,
    "get_structured_notes": get_structured_notes,
    "get_insurance_products": get_insurance_products,
    "quote_insurance": quote_insurance,
    "confirm_insurance_policy": confirm_insurance_policy,
    "get_insurance_claims_info": get_insurance_claims_info,
    "file_insurance_claim": file_insurance_claim,
    "get_financial_diagnosis": get_financial_diagnosis,
    "set_financial_goal": set_financial_goal,
    "get_financial_goals": get_financial_goals,
    "contribute_to_goal": contribute_to_goal,
    "get_habit_tips": get_habit_tips,
    "get_expenses_summary": get_expenses_summary,
    "get_movements": get_movements,
    "get_balance": get_balance,
    "create_expense_limit": create_expense_limit,
    "get_card_payment_info": get_card_payment_info,
    "schedule_payment": schedule_payment,
    "create_shared_expense_group": create_shared_expense_group,
    "add_shared_expense": add_shared_expense,
}
