"""
Carga datos sinteticos de demo. Se ejecuta al iniciar la app si la DB esta vacia.
"""
from datetime import datetime, timedelta
import hashlib
from .database import SessionLocal, engine, Base
from .models import (
    User, Account, Movement, CreditAccount, ExpenseLimit, InvestmentProfile,
    Investment, InvestmentProduct, InvestmentTransaction, PortfolioSnapshot,
    Payee,
)


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def ensure_demo_payees(db, user: User) -> None:
    """Agrega destinatarios demo sin duplicarlos en reinicios posteriores."""
    payees = [
        ("Ana Lopez", "**** 1842"),
        ("Carlos Ramirez", "**** 9307"),
        ("Renta departamento", "**** 6615"),
    ]
    existing_labels = {
        row.label for row in db.query(Payee).filter(Payee.user_id == user.id).all()
    }
    db.add_all([
        Payee(user_id=user.id, label=label, masked_account=masked_account)
        for label, masked_account in payees
        if label not in existing_labels
    ])


def ensure_investment_demo_data(db, user: User) -> None:
    """Completa de forma idempotente el seguimiento de inversiones demo."""
    products = [
        ("cetes", "CETES", "Deuda gubernamental de corto plazo.", "bajo", 9.8, 100),
        ("fondo_deuda", "Fondo de deuda", "Portafolio diversificado de deuda.", "bajo", 10.4, 1000),
        ("portafolio_balanceado", "Portafolio balanceado", "Mezcla de deuda y renta variable.", "medio", 12.1, 5000),
        ("portafolio_dinamico", "Portafolio dinamico", "Mayor potencial con mayor variacion.", "alto", 15.5, 5000),
    ]
    for product_id, title, description, risk, rate, minimum in products:
        if not db.get(InvestmentProduct, product_id):
            db.add(InvestmentProduct(
                id=product_id,
                title=title,
                description=description,
                risk_level=risk,
                annual_rate=rate,
                min_amount=minimum,
            ))

    positions = (
        db.query(Investment)
        .filter(Investment.user_id == user.id, Investment.status == "activo")
        .order_by(Investment.id)
        .all()
    )
    product_ids = {
        "Pagare Banorte 90 dias": "pagare_90",
        "Fondo Balanceado Plus": "fondo_balanceado",
        "CETES": "cetes",
        "Fondo de deuda": "fondo_deuda",
    }
    for index, position in enumerate(positions):
        position.product_id = position.product_id or product_ids.get(position.product)
        position.opened_at = position.opened_at or position.created_at or datetime.utcnow()
        position.updated_at = position.updated_at or datetime.utcnow()
        if position.current_value is None:
            position.current_value = round((position.amount or 0) * (1.025 + index * 0.005), 2)

    if positions and not db.query(InvestmentTransaction).filter(
        InvestmentTransaction.user_id == user.id
    ).first():
        db.add_all([
            InvestmentTransaction(
                user_id=user.id,
                investment_id=position.id,
                transaction_type="deposit",
                amount=position.amount,
                description=f"Aportacion inicial a {position.product}",
                occurred_at=position.opened_at,
            )
            for position in positions
        ])

    if positions and not db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user.id
    ).first():
        snapshot_rows = [
            {
                "id": position.id,
                "productId": position.product_id,
                "product": position.product,
                "amount": round(position.amount or 0, 2),
                "currentValue": round(position.current_value or position.amount or 0, 2),
            }
            for position in positions
        ]
        total_invested = round(sum(row["amount"] for row in snapshot_rows), 2)
        total_value = round(sum(row["currentValue"] for row in snapshot_rows), 2)
        db.add(PortfolioSnapshot(
            user_id=user.id,
            total_invested=total_invested,
            total_value=total_value,
            total_gain=round(total_value - total_invested, 2),
            positions=snapshot_rows,
        ))


def seed_if_empty():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_user = db.query(User).first()
        if existing_user:
            ensure_investment_demo_data(db, existing_user)
            ensure_demo_payees(db, existing_user)
            db.commit()
            return

        user = User(
            clave_bancaria="4152",
            password_hash=hash_pw("demo1234"),
            full_name="Alejo Martinez",
            onboarding_done=False,
        )
        db.add(user)
        db.flush()

        account = Account(
            user_id=user.id,
            label="Cuenta principal",
            masked_number="**** 7788",
            balance=24350.75,
        )
        db.add(account)
        db.flush()

        ensure_demo_payees(db, user)

        categories = [
            ("Comida", 38, "#EB0029"),
            ("Transporte", 22, "#2E7BE5"),
            ("Entretenimiento", 18, "#7B4FE0"),
            ("Otros", 22, "#9AA0A6"),
        ]
        today = datetime.utcnow()
        movements_seed = [
            ("Restaurante La Nacional", "Comida", -450.0, 0),
            ("Uber", "Transporte", -180.0, 1),
            ("Cinepolis", "Entretenimiento", -220.0, 2),
            ("Supermercado Soriana", "Comida", -980.0, 3),
            ("Netflix", "Entretenimiento", -219.0, 5),
            ("Gasolina", "Transporte", -700.0, 6),
            ("Cafeteria", "Comida", -95.0, 0),
            ("Farmacia", "Otros", -340.0, 4),
            ("Deposito nomina", "Ingreso", 18500.0, 10),
            ("Renta", "Otros", -6500.0, 8),
        ]
        for desc, cat, amt, days_ago in movements_seed:
            db.add(Movement(
                account_id=account.id,
                date=today - timedelta(days=days_ago),
                description=desc,
                category=cat,
                amount=amt,
            ))

        credit = CreditAccount(
            user_id=user.id,
            label="Tarjeta de credito",
            masked_number="**** 4521",
            balance=18400.0,
            credit_limit=50000.0,
            current_cat=42.8,
        )
        db.add(credit)

        db.add(ExpenseLimit(
            user_id=user.id, category="Comida",
            monthly_limit=3500.0, alert_threshold_pct=80, current_usage=2940.0,
        ))

        db.add(InvestmentProfile(user_id=user.id, risk_profile=None))

        db.add_all([
            Investment(
                user_id=user.id, product="Pagare Banorte 90 dias", amount=15000.0,
                term_months=3, estimated_rate=9.5, status="activo",
                category="renta_fija", details={"issuer": "Banorte"},
            ),
            Investment(
                user_id=user.id, product="Fondo Balanceado Plus", amount=10000.0,
                term_months=12, estimated_rate=12.4, status="activo",
                category="fondos", details={"riskLevel": "medio"},
            ),
        ])

        ensure_investment_demo_data(db, user)

        db.commit()
    finally:
        db.close()
