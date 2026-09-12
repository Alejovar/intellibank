"""
Carga datos sinteticos de demo. Se ejecuta al iniciar la app si la DB esta vacia.
"""
from datetime import datetime, timedelta
import hashlib
from .database import SessionLocal, engine, Base
from .models import (
    User, Account, Movement, CreditAccount, ExpenseLimit, InvestmentProfile
)


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def seed_if_empty():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).first():
            return  # ya existe data

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

        db.commit()
    finally:
        db.close()
