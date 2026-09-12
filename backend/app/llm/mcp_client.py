"""Cliente MCP sincrono respaldado por una sesion stdio asincrona persistente."""
from __future__ import annotations

import asyncio
from concurrent.futures import TimeoutError as FutureTimeoutError
import json
import logging
import os
from pathlib import Path
import sys
import threading
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

logger = logging.getLogger("banorte.mcp_client")

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_START_TIMEOUT_SECONDS = 15
_CALL_TIMEOUT_SECONDS = 30
_SHUTDOWN_TIMEOUT_SECONDS = 10


class _PersistentMCPClient:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop_event: asyncio.Event | None = None
        self._session: ClientSession | None = None
        self._startup_error: str | None = None

    def start(self) -> str | None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                if self._session is not None:
                    return None
                return self._startup_error or "el cliente MCP aun no esta disponible"

            self._ready.clear()
            self._startup_error = None
            self._session = None
            self._thread = threading.Thread(
                target=self._thread_main,
                name="intellibank-mcp-client",
                daemon=True,
            )
            self._thread.start()

            if not self._ready.wait(_START_TIMEOUT_SECONDS):
                return "timeout iniciando el cliente MCP"
            return self._startup_error

    def _thread_main(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self._serve())
        except Exception as exc:  # noqa: BLE001
            self._startup_error = str(exc)
            logger.exception("La sesion MCP termino inesperadamente")
            self._ready.set()
        finally:
            self._session = None
            self._stop_event = None
            self._loop = None
            loop.close()

    async def _serve(self) -> None:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.mcp_server"],
            cwd=_BACKEND_DIR,
            env=dict(os.environ),
        )
        self._stop_event = asyncio.Event()
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                self._session = session
                self._ready.set()
                # A short timer also keeps cross-thread submissions responsive
                # in runtimes where the selector's self-pipe wakeup is limited.
                while not self._stop_event.is_set():
                    await asyncio.sleep(0.1)

    async def _call(self, name: str, user_id: int, arguments: dict[str, Any]) -> dict:
        if self._session is None:
            raise RuntimeError("la sesion MCP no esta disponible")
        payload = dict(arguments)
        payload["user_id"] = user_id
        response = await self._session.call_tool(name, arguments=payload)
        text_blocks = [block.text for block in response.content if isinstance(block, TextContent)]
        if not text_blocks:
            raise ValueError("respuesta MCP sin contenido de texto")

        result = json.loads(text_blocks[0])
        if not isinstance(result, dict):
            raise ValueError("respuesta MCP no contiene un objeto JSON")
        return result

    def call(self, name: str, user_id: int, arguments: dict[str, Any]) -> dict:
        startup_error = self.start()
        if startup_error:
            return {"error": f"no se pudo iniciar MCP: {startup_error}"}

        loop = self._loop
        if loop is None or self._session is None:
            return {"error": "la sesion MCP no esta disponible"}

        future = asyncio.run_coroutine_threadsafe(
            self._call(name, user_id, arguments),
            loop,
        )
        try:
            return future.result(timeout=_CALL_TIMEOUT_SECONDS)
        except FutureTimeoutError:
            future.cancel()
            return {"error": f"timeout ejecutando tool MCP: {name}"}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error de transporte/protocolo MCP ejecutando %s", name)
            return {"error": f"error MCP ejecutando {name}: {exc}"}

    def shutdown(self) -> None:
        with self._lock:
            loop = self._loop
            stop_event = self._stop_event
            thread = self._thread

        if loop is not None and stop_event is not None and loop.is_running():
            loop.call_soon_threadsafe(stop_event.set)
        if thread is not None and thread.is_alive():
            thread.join(timeout=_SHUTDOWN_TIMEOUT_SECONDS)
            if thread.is_alive():
                logger.warning("El thread del cliente MCP no termino dentro del timeout")

        with self._lock:
            if self._thread is thread and (thread is None or not thread.is_alive()):
                self._thread = None


_client = _PersistentMCPClient()


def start() -> None:
    """Inicia anticipadamente la sesion; las llamadas tambien la inician lazy."""
    error = _client.start()
    if error:
        logger.error("No se pudo iniciar el cliente MCP: %s", error)


def call_domain_tool(name: str, user_id: int, arguments: dict[str, Any]) -> dict:
    return _client.call(name, user_id, arguments)


def shutdown() -> None:
    _client.shutdown()
