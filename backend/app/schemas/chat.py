from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, model_validator
from .a2ui import A2UIEnvelope


class LoginRequest(BaseModel):
    identifier: str | None = None
    # Compatibilidad temporal con el login de la demo anterior.
    clave_bancaria: str | None = None
    password: str = Field(min_length=8)

    @property
    def login_identifier(self) -> str:
        return self.identifier or self.clave_bancaria or ""


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=160)
    phone: str = Field(min_length=7, max_length=30)
    password: str = Field(min_length=8, max_length=128)
    clave_bancaria: str | None = None
    card_number: str | None = None

    @model_validator(mode="after")
    def validate_login_identifier(self):
        if not (self.clave_bancaria or self.card_number):
            raise ValueError("Debes registrar una CLABE o tarjeta")
        return self


class LoginResponse(BaseModel):
    token: str
    full_name: str
    onboarding_done: bool
    biometric_enabled: bool = False


class RegisterResponse(BaseModel):
    token: str
    full_name: str
    onboarding_done: bool
    biometric_enabled: bool = False


class BiometricEnrollRequest(BaseModel):
    platform: Literal["ios", "android", "web"]
    credential_id: str = Field(min_length=8, max_length=256)
    device_name: str | None = Field(default=None, max_length=120)


class PasskeyRegistrationRequest(BaseModel):
    credential: dict[str, Any]
    platform: Literal["ios", "android", "web"] = "web"
    device_name: str | None = Field(default=None, max_length=120)


class PasskeyAuthenticationOptionsRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=160)


class PasskeyAuthenticationRequest(PasskeyAuthenticationOptionsRequest):
    credential: dict[str, Any]


class ChatMessageRequest(BaseModel):
    message: str
    input_mode: Literal["text", "voice", "button"] = "text"
    active_categories: list[str] = []


class ChatTextResponse(BaseModel):
    mime_type: Literal["text/plain"] = "text/plain"
    payload: str


class ChatResponse(BaseModel):
    response: A2UIEnvelope | ChatTextResponse


class ActionExecuteRequest(BaseModel):
    tool: str
    args: dict[str, Any] = {}
    screen_id: Optional[str] = None


class SaveScreenRequest(BaseModel):
    title: str
    a2ui_payload: dict[str, Any]
