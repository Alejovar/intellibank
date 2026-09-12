"""
Carga datos sinteticos de demo. Se ejecuta al iniciar la app si la DB esta vacia.
"""
from datetime import datetime, timedelta
import hashlib
from .database import SessionLocal, engine, Base, ensure_sqlite_schema
from .models import (
    User, Account, Movement, CreditAccount, ExpenseLimit, InvestmentProfile,
    Investment, InvestmentProduct, InvestmentTransaction, PortfolioSnapshot,
)


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def ensure_investment_demo_data(db, user: User) -> None:
    """Completa la demo de inversiones en bases creadas por versiones anteriores."""
    products = [
        ("cetes", "CETES", "Deuda gubernamental de corto plazo.", "bajo", 9.8, 100),
        ("fondo_deuda", "Fondo de deuda", "Portafolio diversificado de deuda.", "bajo", 10.4, 1000),
        ("portafolio_balanceado", "Portafolio balanceado", "Mezcla de deuda y renta variable.", "medio", 12.1, 5000),
        ("portafolio_dinamico", "Portafolio dinamico", "Mayor potencial con mayor variacion.", "alto", 15.5, 5000),
    ]
    for product_id, title, description, risk, rate, minimum in products:
        if not db.get(InvestmentProduct, product_id):
            db.add(InvestmentProduct(
                id=product_id, title=title, description=description,
                risk_level=risk, annual_rate=rate, min_amount=minimum,
            ))

    profile = db.query(InvestmentProfile).filter(InvestmentProfile.user_id == user.id).first()
    if not profile:
        db.add(InvestmentProfile(user_id=user.id, risk_profile=None))

    if db.query(Investment).filter(Investment.user_id == user.id).first():
        return

    today = datetime.utcnow()
    cetes = Investment(
        user_id=user.id, product_id="cetes", product="CETES", amount=10000,
        current_value=10840, term_months=12, estimated_rate=9.8, status="activo",
        opened_at=today - timedelta(days=210),
    )
    fondo = Investment(
        user_id=user.id, product_id="fondo_deuda", product="Fondo de deuda", amount=7500,
        current_value=7815, term_months=18, estimated_rate=10.4, status="activo",
        opened_at=today - timedelta(days=150),
    )
    db.add_all([cetes, fondo])
    db.flush()
    db.add_all([
        InvestmentTransaction(
            user_id=user.id, investment_id=cetes.id, transaction_type="deposit",
            amount=10000, description="Aportacion inicial a CETES", occurred_at=cetes.opened_at,
        ),
        InvestmentTransaction(
            user_id=user.id, investment_id=fondo.id, transaction_type="deposit",
            amount=7500, description="Aportacion inicial a Fondo de deuda", occurred_at=fondo.opened_at,
        ),
        PortfolioSnapshot(
            user_id=user.id, total_invested=17500, total_value=18655, total_gain=1155,
            positions=[
                {"productId": "cetes", "product": "CETES", "amount": 10000, "currentValue": 10840},
                {"productId": "fondo_deuda", "product": "Fondo de deuda", "amount": 7500, "currentValue": 7815},
            ],
            captured_at=today - timedelta(days=30),
        ),
    ])


def seed_if_empty():
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema()
    db = SessionLocal()
    try:
        existing_user = db.query(User).first()
        if existing_user:
            ensure_investment_demo_data(db, existing_user)
            db.commit()
            return

        user = User(
            clave_bancaria="4152",
            password_hash=hash_pw("demo1234"),
            full_name="Alejo Martinez",
            email="alejo@demo.local",
            phone="5512345678",
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

        products = [
            InvestmentProduct(
                id="cetes", title="CETES", description="Deuda gubernamental de corto plazo.",
                risk_level="bajo", annual_rate=9.8, min_amount=100,
            ),
            InvestmentProduct(
                id="fondo_deuda", title="Fondo de deuda", description="Portafolio diversificado de deuda.",
                risk_level="bajo", annual_rate=10.4, min_amount=1000,
            ),
            InvestmentProduct(
                id="portafolio_balanceado", title="Portafolio balanceado", description="Mezcla de deuda y renta variable.",
                risk_level="medio", annual_rate=12.1, min_amount=5000,
            ),
            InvestmentProduct(
                id="portafolio_dinamico", title="Portafolio dinamico", description="Mayor potencial con mayor variacion.",
                risk_level="alto", annual_rate=15.5, min_amount=5000,
            ),
        ]
        db.add_all(products)

        cetes = Investment(
            user_id=user.id, product_id="cetes", product="CETES", amount=10000,
            current_value=10840, term_months=12, estimated_rate=9.8, status="activo",
            opened_at=today - timedelta(days=210),
        )
        fondo = Investment(
            user_id=user.id, product_id="fondo_deuda", product="Fondo de deuda", amount=7500,
            current_value=7815, term_months=18, estimated_rate=10.4, status="activo",
            opened_at=today - timedelta(days=150),
        )
        db.add_all([cetes, fondo])
        db.flush()
        db.add_all([
            InvestmentTransaction(
                user_id=user.id, investment_id=cetes.id, transaction_type="deposit",
                amount=10000, description="Aportacion inicial a CETES",
                occurred_at=cetes.opened_at,
            ),
            InvestmentTransaction(
                user_id=user.id, investment_id=fondo.id, transaction_type="deposit",
                amount=7500, description="Aportacion inicial a Fondo de deuda",
                occurred_at=fondo.opened_at,
            ),
        ])
        db.add(PortfolioSnapshot(
            user_id=user.id,
            total_invested=17500,
            total_value=18655,
            total_gain=1155,
            positions=[
                {"productId": "cetes", "product": "CETES", "amount": 10000, "currentValue": 10840},
                {"productId": "fondo_deuda", "product": "Fondo de deuda", "amount": 7500, "currentValue": 7815},
            ],
            captured_at=today - timedelta(days=30),
        ))

        db.commit()
    finally:
        db.close()
