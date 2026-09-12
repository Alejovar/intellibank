from typing import Any, Literal, Optional
from pydantic import BaseModel
from .a2ui import A2UIEnvelope


class LoginRequest(BaseModel):
    clave_bancaria: str
    password: str


class LoginResponse(BaseModel):
    token: str
    full_name: str
    onboarding_done: bool


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
