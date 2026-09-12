from openai import OpenAI
from ..config import get_settings

_settings = get_settings()
_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not _settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY no esta configurada. Copia .env.example a .env "
                "y agrega tu llave."
            )
        _client = OpenAI(api_key=_settings.openai_api_key)
    return _client


def get_model() -> str:
    return _settings.openai_model
