"""
Auth minima para demo: identificador de cuenta + password contra la DB sintetica.
Emite un token simple (no es JWT real, es suficiente para el hackathon;
en produccion usar JWT firmado / OAuth interno de Banorte).
"""
import hashlib
import secrets
import re
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Header
from .database import get_db
from .models import AuthDevice, User

_SESSIONS: dict[str, int] = {}  # token -> user_id (en memoria; usar Redis en prod)


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def login(clave_bancaria: str, password: str, db: Session) -> tuple[str, User]:
    user = find_user(clave_bancaria, db)
    if not user or user.password_hash != hash_pw(password):
        raise HTTPException(status_code=401, detail="Cuenta o contraseña incorrectas")
    token = secrets.token_hex(16)
    _SESSIONS[token] = user.id
    return token, user


def create_session(user: User) -> str:
    token = secrets.token_hex(16)
    _SESSIONS[token] = user.id
    return token


def _normalize_identifier(value: str) -> str:
    return re.sub(r"\s+", "", value or "").lower()


def _normalize_card(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def find_user(identifier: str, db: Session) -> User | None:
    normalized = _normalize_identifier(identifier)
    user = db.query(User).filter(User.clave_bancaria == normalized).first()
    if user:
        return user
    user = db.query(User).filter(User.email == normalized).first()
    if user:
        return user
    digits = _normalize_card(identifier)
    if len(digits) == 10:
        user = db.query(User).filter(User.phone == digits).first()
        if user:
            return user
    card_hash = hashlib.sha256(digits.encode()).hexdigest()
    return db.query(User).filter(User.card_number_hash == card_hash).first()


def register(
    full_name: str,
    email: str,
    phone: str,
    password: str,
    clave_bancaria: str | None,
    card_number: str | None,
    db: Session,
) -> User:
    normalized_email = _normalize_identifier(email)
    normalized_phone = _normalize_card(phone)
    normalized_clave = _normalize_identifier(clave_bancaria or "")
    normalized_card = _normalize_card(card_number or "")
    if not normalized_clave and not normalized_card:
        raise HTTPException(status_code=422, detail="Debes registrar una CLABE o tarjeta")
    if db.query(User).filter(User.email == normalized_email).first():
        raise HTTPException(status_code=409, detail="El correo ya esta registrado")
    if db.query(User).filter(User.phone == normalized_phone).first():
        raise HTTPException(status_code=409, detail="El telefono ya esta registrado")
    if normalized_clave and db.query(User).filter(User.clave_bancaria == normalized_clave).first():
        raise HTTPException(status_code=409, detail="La CLABE ya esta registrada")
    card_hash = hashlib.sha256(normalized_card.encode()).hexdigest() if normalized_card else None
    if card_hash and db.query(User).filter(User.card_number_hash == card_hash).first():
        raise HTTPException(status_code=409, detail="La tarjeta ya esta registrada")
    user = User(
        clave_bancaria=normalized_clave or f"usr{secrets.token_hex(8)}",
        password_hash=hash_pw(password),
        full_name=full_name.strip(),
        email=normalized_email,
        phone=normalized_phone,
        card_number_hash=card_hash,
        card_last4=normalized_card[-4:] if normalized_card else None,
        onboarding_done=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def enroll_device(
    user: User,
    platform: str,
    credential_id: str,
    device_name: str | None,
    db: Session,
) -> AuthDevice:
    if platform not in {"ios", "android", "web"}:
        raise HTTPException(status_code=422, detail="Plataforma biometrica invalida")
    if not credential_id.strip():
        raise HTTPException(status_code=422, detail="Falta la credencial del dispositivo")
    device = db.query(AuthDevice).filter(AuthDevice.credential_id == credential_id).first()
    if device and device.user_id != user.id:
        raise HTTPException(status_code=409, detail="La credencial ya pertenece a otro usuario")
    if not device:
        device = AuthDevice(
            user_id=user.id,
            platform=platform,
            credential_id=credential_id.strip(),
            device_name=device_name,
        )
        db.add(device)
    else:
        device.last_used_at = datetime.utcnow()
    user.biometric_enabled = True
    db.commit()
    db.refresh(device)
    return device


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    token = authorization.removeprefix("Bearer ").strip()
    user_id = _SESSIONS.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user
