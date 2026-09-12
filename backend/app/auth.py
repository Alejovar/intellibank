"""
Auth minima para demo: clave bancaria + password contra la DB sintetica.
Emite un token simple (no es JWT real, es suficiente para el hackathon;
en produccion usar JWT firmado / OAuth interno de Banorte).
"""
import hashlib
import secrets
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Header
from .database import get_db
from .models import User

_SESSIONS: dict[str, int] = {}  # token -> user_id (en memoria; usar Redis en prod)


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def login(clave_bancaria: str, password: str, db: Session) -> tuple[str, User]:
    user = db.query(User).filter(User.clave_bancaria == clave_bancaria).first()
    if not user or user.password_hash != hash_pw(password):
        raise HTTPException(status_code=401, detail="Clave bancaria o password incorrectos")
    token = secrets.token_hex(16)
    _SESSIONS[token] = user.id
    return token, user


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
