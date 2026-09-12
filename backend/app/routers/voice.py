"""Transcripcion opcional para clientes que no tienen reconocimiento nativo."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from .. import auth as auth_module
from ..llm.client import transcribe_audio

router = APIRouter(prefix="/voice", tags=["voice"])
MAX_AUDIO_BYTES = 12 * 1024 * 1024
ALLOWED_TYPES = {
    "audio/m4a", "audio/mp4", "audio/mpeg", "audio/mp3", "audio/wav",
    "audio/webm", "audio/x-m4a", "application/octet-stream",
}


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile,
    user=Depends(auth_module.get_current_user),
):
    del user  # La dependencia protege el endpoint; la transcripcion no necesita user_id.
    if audio.content_type and audio.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Formato de audio no soportado")
    content = await audio.read(MAX_AUDIO_BYTES + 1)
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="El audio excede el limite permitido")
    if not content:
        raise HTTPException(status_code=422, detail="El audio esta vacio")
    try:
        text = transcribe_audio(
            content,
            filename=audio.filename or "dictado.m4a",
            content_type=audio.content_type,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"text": text, "model": "gpt-4o-mini-transcribe"}
