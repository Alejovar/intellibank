import os
import tempfile
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth import _session_user_id, create_session, hash_pw, login, register, verify_pw
from app.database import Base
from app.llm.tools import (
    calculate_performance,
    compare_investments,
    get_investment_cashflows,
    get_portfolio,
)
from app.models import (
    Investment,
    InvestmentProduct,
    InvestmentProfile,
    InvestmentTransaction,
    User,
)
from app.passkeys import registration_options


class InvestmentModuleTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.user = User(
            clave_bancaria="123456789012345678",
            password_hash=hash_pw("password123"),
            full_name="Usuario Inversionista",
            email="inversionista@example.com",
            phone="5512345678",
        )
        self.db.add(self.user)
        self.db.flush()
        self.db.add(InvestmentProfile(user_id=self.user.id, risk_profile="conservador"))
        self.db.add_all([
            InvestmentProduct(
                id="cetes", title="CETES", description="Deuda gubernamental",
                risk_level="bajo", annual_rate=9.8, min_amount=100,
            ),
            InvestmentProduct(
                id="fondo_deuda", title="Fondo de deuda", description="Fondo diversificado",
                risk_level="bajo", annual_rate=10.4, min_amount=1000,
            ),
        ])
        position = Investment(
            user_id=self.user.id, product_id="cetes", product="CETES", amount=10000,
            current_value=10840, term_months=12, estimated_rate=9.8, status="activo",
        )
        self.db.add(position)
        self.db.flush()
        self.db.add(InvestmentTransaction(
            user_id=self.user.id, investment_id=position.id,
            transaction_type="deposit", amount=10000, description="Aportacion inicial",
        ))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        os.unlink(self.db_path)

    def test_portfolio_performance_and_cashflows(self):
        portfolio = get_portfolio(self.db, self.user.id)
        self.assertEqual(portfolio["totalValue"], 10840)
        self.assertEqual(portfolio["totalGain"], 840)
        self.assertEqual(len(portfolio["positions"]), 1)

        performance = calculate_performance(self.db, self.user.id)
        self.assertEqual(performance["returnPct"], 8.4)
        self.assertEqual(performance["trend"], "positive")

        cashflows = get_investment_cashflows(self.db, self.user.id)
        self.assertEqual(cashflows["totalDeposits"], 10000)

    def test_compare_uses_catalog_rates(self):
        result = compare_investments(
            self.db, self.user.id, ["cetes", "fondo_deuda"], 5000, 12
        )
        self.assertEqual(len(result["products"]), 2)
        self.assertEqual(result["products"][0]["rate"], 9.8)

    def test_registration_and_legacy_login(self):
        new_user = register(
            full_name="Nueva Persona",
            email="nueva@example.com",
            phone="5587654321",
            password="password123",
            clave_bancaria="987654321012345678",
            card_number=None,
            db=self.db,
        )
        self.assertTrue(verify_pw("password123", new_user.password_hash))
        token, logged_user = login("nueva@example.com", "password123", self.db)
        self.assertTrue(token)
        self.assertEqual(logged_user.id, new_user.id)

    def test_signed_session_survives_process_memory(self):
        token = create_session(self.user)
        self.assertIn(".", token)
        self.assertEqual(_session_user_id(token), self.user.id)
        self.assertIsNone(_session_user_id(f"{token}alterado"))

    def test_passkey_registration_requires_platform_biometric(self):
        options = registration_options(self.user, self.db)
        self.assertEqual(options["rp"]["id"], "localhost")
        self.assertEqual(options["authenticatorSelection"]["authenticatorAttachment"], "platform")
        self.assertEqual(options["authenticatorSelection"]["userVerification"], "required")


if __name__ == "__main__":
    unittest.main()
