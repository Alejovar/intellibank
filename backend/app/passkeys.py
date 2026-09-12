"""Ceremonias WebAuthn para Face ID, biometria Android y Windows Hello.

El servidor conserva unicamente la clave publica y el contador de firma de la
credencial. Los datos biometricos nunca salen del autenticador del dispositivo.
"""
import json
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session
from webauthn import (
    base64url_to_bytes,
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from .config import get_settings
from .models import AuthDevice, User


settings = get_settings()
_CHALLENGE_TTL = timedelta(minutes=5)
_registration_challenges: dict[int, tuple[bytes, datetime]] = {}
_authentication_challenges: dict[int, tuple[bytes, datetime]] = {}


def _save_challenge(store: dict, user_id: int, challenge: bytes) -> None:
    store[user_id] = (challenge, datetime.utcnow() + _CHALLENGE_TTL)


def _take_challenge(store: dict, user_id: int) -> bytes:
    item = store.pop(user_id, None)
    if not item or item[1] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="El reto biometrico expiro; intenta de nuevo")
    return item[0]


def registration_options(user: User, db: Session) -> dict:
    existing = db.query(AuthDevice).filter(
        AuthDevice.user_id == user.id,
        AuthDevice.credential_public_key.is_not(None),
    ).all()
    options = generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_id=str(user.id).encode("utf-8"),
        user_name=user.email or user.clave_bancaria,
        user_display_name=user.full_name,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(device.credential_id))
            for device in existing
        ],
    )
    _save_challenge(_registration_challenges, user.id, options.challenge)
    return json.loads(options_to_json(options))


def complete_registration(
    user: User,
    credential: dict,
    platform: str,
    device_name: str | None,
    db: Session,
) -> AuthDevice:
    challenge = _take_challenge(_registration_challenges, user.id)
    try:
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origin,
            require_user_verification=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="No se pudo verificar la biometria") from exc

    credential_id = bytes_to_base64url(verification.credential_id)
    device = db.query(AuthDevice).filter(AuthDevice.credential_id == credential_id).first()
    if device and device.user_id != user.id:
        raise HTTPException(status_code=409, detail="La credencial pertenece a otra cuenta")
    transports = credential.get("response", {}).get("transports", [])
    if not device:
        device = AuthDevice(user_id=user.id, platform=platform, credential_id=credential_id)
        db.add(device)
    device.credential_public_key = verification.credential_public_key
    device.sign_count = verification.sign_count
    device.transports = transports
    device.device_name = device_name
    device.last_used_at = datetime.utcnow()
    user.biometric_enabled = True
    db.commit()
    db.refresh(device)
    return device


def authentication_options(user: User, db: Session) -> dict:
    devices = db.query(AuthDevice).filter(
        AuthDevice.user_id == user.id,
        AuthDevice.credential_public_key.is_not(None),
    ).all()
    if not devices:
        raise HTTPException(status_code=404, detail="Este dispositivo aun no tiene acceso biometrico")
    options = generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(device.credential_id))
            for device in devices
        ],
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    _save_challenge(_authentication_challenges, user.id, options.challenge)
    return json.loads(options_to_json(options))


def complete_authentication(user: User, credential: dict, db: Session) -> AuthDevice:
    challenge = _take_challenge(_authentication_challenges, user.id)
    credential_id = credential.get("id", "")
    device = db.query(AuthDevice).filter(
        AuthDevice.user_id == user.id,
        AuthDevice.credential_id == credential_id,
        AuthDevice.credential_public_key.is_not(None),
    ).first()
    if not device:
        raise HTTPException(status_code=401, detail="Credencial biometrica desconocida")
    try:
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origin,
            credential_public_key=device.credential_public_key,
            credential_current_sign_count=device.sign_count or 0,
            require_user_verification=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="La verificacion biometrica fallo") from exc
    device.sign_count = verification.new_sign_count
    device.last_used_at = datetime.utcnow()
    db.commit()
    return device
