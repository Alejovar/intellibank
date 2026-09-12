"""
Autenticacion de la demo: password o passkey contra la DB sintetica.
Los tokens de sesion estan firmados y sobreviven reinicios del servidor.
"""
import base64
import hashlib
import hmac
import re
import secrets
import time
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Header
from .database import get_db
from .config import get_settings
from .models import AuthDevice, User

_PBKDF2_ITERATIONS = 310_000
_SESSION_TTL_SECONDS = 60 * 60 * 24
settings = get_settings()


def hash_pw(pw: str) -> str:
    """Hash de contrasena para cuentas nuevas; conserva soporte legacy para la demo."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", pw.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_pw(pw: str, stored: str) -> bool:
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt_hex, digest_hex = stored.split("$", 3)
            digest = hashlib.pbkdf2_hmac(
                "sha256", pw.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
            )
            return hmac.compare_digest(digest.hex(), digest_hex)
        except (ValueError, TypeError):
            return False
    # Usuarios sembrados de la primera version de la demo.
    return hmac.compare_digest(hashlib.sha256(pw.encode()).hexdigest(), stored)


def normalize_identifier(value: str) -> str:
    return re.sub(r"\s+", "", value or "").lower()


def normalize_card(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _find_user(identifier: str, db: Session) -> User | None:
    normalized = normalize_identifier(identifier)
    user = db.query(User).filter(User.clave_bancaria == normalized).first()
    if user:
        return user
    user = db.query(User).filter(User.email == normalized).first()
    if user:
        return user
    card_hash = hashlib.sha256(normalize_card(identifier).encode()).hexdigest()
    return db.query(User).filter(User.card_number_hash == card_hash).first()


def login(identifier: str, password: str, db: Session) -> tuple[str, User]:
    user = _find_user(identifier, db)
    if not user or not verify_pw(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Clave bancaria o password incorrectos")
    return create_session(user), user


def find_user(identifier: str, db: Session) -> User | None:
    return _find_user(identifier, db)


def create_session(user: User) -> str:
    expires_at = int(time.time()) + _SESSION_TTL_SECONDS
    payload = f"{user.id}:{expires_at}".encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(
        settings.jwt_secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256
    ).hexdigest()
    return f"{encoded}.{signature}"


def _session_user_id(token: str) -> int | None:
    try:
        encoded, signature = token.split(".", 1)
        expected = hmac.new(
            settings.jwt_secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        padded = encoded + "=" * ((4 - len(encoded) % 4) % 4)
        user_id, expires_at = base64.urlsafe_b64decode(padded).decode("utf-8").split(":", 1)
        if int(expires_at) < int(time.time()):
            return None
        return int(user_id)
    except (ValueError, TypeError):
        return None


def register(
    full_name: str,
    email: str,
    phone: str,
    password: str,
    clave_bancaria: str | None,
    card_number: str | None,
    db: Session,
) -> User:
    normalized_email = normalize_identifier(email)
    normalized_clave = normalize_identifier(clave_bancaria or "")
    normalized_card = normalize_card(card_number or "")
    if not normalized_clave and not normalized_card:
        raise HTTPException(status_code=422, detail="Debes registrar una CLABE o tarjeta")
    if db.query(User).filter(User.email == normalized_email).first():
        raise HTTPException(status_code=409, detail="El correo ya esta registrado")
    if normalized_clave and db.query(User).filter(User.clave_bancaria == normalized_clave).first():
        raise HTTPException(status_code=409, detail="La CLABE ya esta registrada")

    card_hash = hashlib.sha256(normalized_card.encode()).hexdigest() if normalized_card else None
    if card_hash and db.query(User).filter(User.card_number_hash == card_hash).first():
        raise HTTPException(status_code=409, detail="La tarjeta ya esta registrada")

    # La columna legacy es obligatoria; para registros con tarjeta generamos
    # una clave interna que nunca se muestra como dato bancario real.
    internal_clave = normalized_clave or f"usr{secrets.token_hex(8)}"
    user = User(
        clave_bancaria=internal_clave,
        password_hash=hash_pw(password),
        full_name=full_name.strip(),
        email=normalized_email,
        phone=phone.strip(),
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
    user_id = _session_user_id(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user
