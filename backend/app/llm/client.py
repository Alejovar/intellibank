from anthropic import Anthropic
from ..config import get_settings

_settings = get_settings()
_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        if not _settings.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY no esta configurada. Copia .env.example a .env "
                "y agrega tu llave."
            )
        _client = Anthropic(api_key=_settings.anthropic_api_key)
    return _client


def get_model() -> str:
    return _settings.anthropic_model
