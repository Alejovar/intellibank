"""Cliente MCP sincrono para las tools internas de inversiones.

Cada llamada abre una sesion stdio corta. En Windows esto evita que el reload
de Uvicorn deje vivo un thread cuyo subprocess MCP ya fue cerrado. El limite
entre LLM y dominio sigue siendo un intercambio MCP real.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

logger = logging.getLogger("banorte.mcp_client")

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_CALL_TIMEOUT_SECONDS = 30


async def _call_once(name: str, user_id: int, arguments: dict[str, Any]) -> dict:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_server"],
        cwd=_BACKEND_DIR,
        env=dict(os.environ),
    )
    payload = dict(arguments)
    payload["user_id"] = user_id

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            response = await session.call_tool(name, arguments=payload)

    text_blocks = [
        block.text for block in response.content if isinstance(block, TextContent)
    ]
    if not text_blocks:
        raise ValueError("respuesta MCP sin contenido de texto")

    result = json.loads(text_blocks[0])
    if not isinstance(result, dict):
        raise ValueError("respuesta MCP no contiene un objeto JSON")
    return result


def _new_event_loop() -> asyncio.AbstractEventLoop:
    # Uvicorn --reload instala SelectorEventLoop en Windows y ese loop no
    # soporta subprocess_exec. Una sesion MCP stdio necesita Proactor.
    if sys.platform == "win32":
        return asyncio.ProactorEventLoop()
    return asyncio.new_event_loop()


def start() -> None:
    """La sesion se abre de forma lazy por llamada; no hay estado que iniciar."""


def call_domain_tool(name: str, user_id: int, arguments: dict[str, Any]) -> dict:
    loop = _new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            asyncio.wait_for(
                _call_once(name, user_id, arguments),
                timeout=_CALL_TIMEOUT_SECONDS,
            )
        )
    except TimeoutError:
        return {"error": f"timeout ejecutando tool MCP: {name}"}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error de transporte/protocolo MCP ejecutando %s", name)
        return {"error": f"error MCP ejecutando {name}: {exc}"}
    finally:
        asyncio.set_event_loop(None)
        loop.close()


def shutdown() -> None:
    """No-op: las sesiones stdio se cierran al terminar cada llamada."""
