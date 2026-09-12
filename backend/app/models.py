"""
Modelos SQLAlchemy. Todos los datos son sinteticos/hardcodeados para la demo
del hackathon: no representan cuentas ni clientes reales de Banorte.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON
)
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    clave_bancaria = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
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
    product = Column(String)
    amount = Column(Float)
    term_months = Column(Integer)
    estimated_rate = Column(Float)
    status = Column(String, default="simulado")  # simulado | activo


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


class ConversationTurn(Base):
    """Historial de conversacion por usuario, usado para dar contexto al LLM."""
    __tablename__ = "conversation_turns"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    role = Column(String)  # user | assistant | tool_result
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
