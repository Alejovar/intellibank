from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.chat import (
    BiometricEnrollRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    PasskeyAuthenticationOptionsRequest,
    PasskeyAuthenticationRequest,
    PasskeyRegistrationRequest,
)
from .. import auth as auth_module
from .. import passkeys

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    token, user = auth_module.login(body.login_identifier, body.password, db)
    return LoginResponse(
        token=token,
        full_name=user.full_name,
        onboarding_done=user.onboarding_done,
        biometric_enabled=user.biometric_enabled,
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    user = auth_module.register(
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        password=body.password,
        clave_bancaria=body.clave_bancaria,
        card_number=body.card_number,
        db=db,
    )
    token, _ = auth_module.login(user.email or user.clave_bancaria, body.password, db)
    return RegisterResponse(
        token=token,
        full_name=user.full_name,
        onboarding_done=user.onboarding_done,
        biometric_enabled=user.biometric_enabled,
    )


@router.post("/biometric/enroll")
def enroll_biometric(
    body: BiometricEnrollRequest,
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    device = auth_module.enroll_device(
        user=user,
        platform=body.platform,
        credential_id=body.credential_id,
        device_name=body.device_name,
        db=db,
    )
    return {
        "ok": True,
        "platform": device.platform,
        "credential_id": device.credential_id,
        "biometric_enabled": True,
    }


@router.post("/passkey/register/options")
def passkey_registration_options(
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    return passkeys.registration_options(user, db)


@router.post("/passkey/register/complete")
def passkey_registration_complete(
    body: PasskeyRegistrationRequest,
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    device = passkeys.complete_registration(
        user=user,
        credential=body.credential,
        platform=body.platform,
        device_name=body.device_name,
        db=db,
    )
    return {"ok": True, "credential_id": device.credential_id, "biometric_enabled": True}


@router.post("/passkey/login/options")
def passkey_authentication_options(
    body: PasskeyAuthenticationOptionsRequest,
    db: Session = Depends(get_db),
):
    user = auth_module.find_user(body.identifier, db)
    if not user:
        raise HTTPException(status_code=401, detail="Cuenta no encontrada")
    return passkeys.authentication_options(user, db)


@router.post("/passkey/login/complete", response_model=LoginResponse)
def passkey_authentication_complete(
    body: PasskeyAuthenticationRequest,
    db: Session = Depends(get_db),
):
    user = auth_module.find_user(body.identifier, db)
    if not user:
        raise HTTPException(status_code=401, detail="Cuenta no encontrada")
    passkeys.complete_authentication(user, body.credential, db)
    return LoginResponse(
        token=auth_module.create_session(user),
        full_name=user.full_name,
        onboarding_done=user.onboarding_done,
        biometric_enabled=True,
    )


@router.post("/onboarding-complete")
def complete_onboarding(
    db: Session = Depends(get_db),
    user=Depends(auth_module.get_current_user),
):
    user.onboarding_done = True
    db.commit()
    return {"ok": True}
