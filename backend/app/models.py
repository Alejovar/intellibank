"""
Modelos SQLAlchemy. Todos los datos son sinteticos/hardcodeados para la demo
del hackathon: no representan cuentas ni clientes reales de Banorte.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON,
    LargeBinary,
)
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    clave_bancaria = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, nullable=True)
    card_number_hash = Column(String, unique=True, index=True, nullable=True)
    card_last4 = Column(String, nullable=True)
    biometric_enabled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    onboarding_done = Column(Boolean, default=False)

    accounts = relationship("Account", back_populates="owner")
    credit_accounts = relationship("CreditAccount", back_populates="owner")
    generated_screens = relationship("SavedScreen", back_populates="owner")


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    label = Column(String, default="Cuenta principal")
    masked_number = Column(String, default="**** 0000")
    balance = Column(Float, default=0.0)
    currency = Column(String, default="MXN")

    owner = relationship("User", back_populates="accounts")
    movements = relationship("Movement", back_populates="account")


class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(String)
    category = Column(String, default="Otros")
    amount = Column(Float)  # negativo = gasto, positivo = ingreso

    account = relationship("Account", back_populates="movements")


class CreditAccount(Base):
    __tablename__ = "credit_accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    label = Column(String, default="Tarjeta de credito")
    masked_number = Column(String, default="**** 0000")
    balance = Column(Float, default=0.0)
    credit_limit = Column(Float, default=0.0)
    current_cat = Column(Float, default=42.8)  # CAT anual estimado actual
    plan_term_months = Column(Integer, nullable=True)
    plan_monthly_payment = Column(Float, nullable=True)
    plan_cat = Column(Float, nullable=True)

    owner = relationship("User", back_populates="credit_accounts")


class ExpenseLimit(Base):
    __tablename__ = "expense_limits"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category = Column(String)
    monthly_limit = Column(Float)
    alert_threshold_pct = Column(Integer, default=80)
    current_usage = Column(Float, default=0.0)


class ScheduledPayment(Base):
    __tablename__ = "scheduled_payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    credit_account_id = Column(Integer, ForeignKey("credit_accounts.id"))
    amount = Column(Float)
    scheduled_date = Column(DateTime)
    status = Column(String, default="programado")


class InvestmentProfile(Base):
    __tablename__ = "investment_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    risk_profile = Column(String, nullable=True)  # conservador/moderado/dinamico


class Investment(Base):
    __tablename__ = "investments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(String, nullable=True)
    product = Column(String)
    amount = Column(Float)
    current_value = Column(Float, nullable=True)
    term_months = Column(Integer)
    estimated_rate = Column(Float)
    status = Column(String, default="simulado")  # simulado | activo
    category = Column(String, nullable=True)  # general | renta_fija | deuda | ...
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)


class InvestmentTransaction(Base):
    """Movimientos de dinero asociados a una posicion de inversion."""
    __tablename__ = "investment_transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    investment_id = Column(Integer, ForeignKey("investments.id"), nullable=True)
    transaction_type = Column(String, nullable=False)  # deposit | withdrawal | gain | fee
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    occurred_at = Column(DateTime, default=datetime.utcnow, index=True)


class InvestmentProduct(Base):
    """Catalogo de productos que el agente puede recomendar."""
    __tablename__ = "investment_products"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    risk_level = Column(String, nullable=False)
    annual_rate = Column(Float, nullable=False)
    min_amount = Column(Float, default=0.0)
    active = Column(Boolean, default=True, nullable=False)


class PortfolioSnapshot(Base):
    """Foto historica del portafolio para comparaciones antes/despues."""
    __tablename__ = "portfolio_snapshots"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    total_invested = Column(Float, nullable=False, default=0.0)
    total_value = Column(Float, nullable=False, default=0.0)
    total_gain = Column(Float, nullable=False, default=0.0)
    positions = Column(JSON, default=list)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product = Column(String)
    coverage_level = Column(String)
    monthly_premium = Column(Float)
    status = Column(String, default="activa")
    created_at = Column(DateTime, default=datetime.utcnow)


class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("insurance_policies.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(Text)
    status = Column(String, default="en revision")
    created_at = Column(DateTime, default=datetime.utcnow)


class FinancialGoal(Base):
    __tablename__ = "financial_goals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    target_amount = Column(Float)
    target_date = Column(DateTime)
    saved_amount = Column(Float, default=0.0)
    term = Column(String, nullable=True)  # corto | mediano | largo
    created_at = Column(DateTime, default=datetime.utcnow)


class SharedExpenseGroup(Base):
    __tablename__ = "shared_expense_groups"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="Gasto compartido")
    people = Column(JSON, default=list)     # [{"name": "...", "paid": 0, "owes": 0}]
    expenses = Column(JSON, default=list)   # [{"desc": "...", "amount": 0, "paid_by": "..."}]


class SavedScreen(Base):
    __tablename__ = "saved_screens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    a2ui_payload = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="generated_screens")


class InterfaceHistory(Base):
    """Registro reproducible de cada interfaz generada por una pregunta."""
    __tablename__ = "interface_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String, nullable=False)
    user_prompt = Column(Text, nullable=True)
    intent = Column(String, nullable=True)
    tool_names = Column(JSON, default=list)
    tool_args = Column(JSON, default=dict)
    data_snapshot = Column(JSON, default=dict)
    a2ui_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AuthDevice(Base):
    """Metadata de un dispositivo; nunca guarda huellas ni rostros."""
    __tablename__ = "auth_devices"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    platform = Column(String, nullable=False)  # ios | android | web
    credential_id = Column(String, nullable=False, unique=True)
    credential_public_key = Column(LargeBinary, nullable=True)
    sign_count = Column(Integer, default=0, nullable=False)
    transports = Column(JSON, default=list)
    device_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


class ConversationTurn(Base):
    """Historial de conversacion por usuario, usado para dar contexto al LLM."""
    __tablename__ = "conversation_turns"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    role = Column(String)  # user | assistant | tool
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class SessionState(Base):
    """Estado autoritativo del flujo A2UI activo para un usuario."""
    __tablename__ = "session_states"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    current_stage = Column(String, default="idle")
    last_screen_id = Column(String, nullable=True)
    last_screen_payload = Column(JSON, nullable=True)
    pending_action = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
