from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_transcription_model: str = "gpt-4o-mini-transcribe"
    database_url: str = "sqlite:///./banorte_demo.db"
    jwt_secret: str = "dev-secret-change-me"
    cors_origins: str = "http://localhost:5173"
    webauthn_rp_id: str = "localhost"
    webauthn_rp_name: str = "Banca AI"
    webauthn_origin: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

    @property
    def cors_origin_list(self):
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> "Settings":
    return Settings()
