"""Servidor MCP interno para ejecutar las tools de dominio sobre SQLite."""
from __future__ import annotations

import asyncio
import copy
import json
import logging
from typing import Any

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .database import SessionLocal
from .llm.tool_specs import INVESTMENT_DOMAIN_TOOL_NAMES, INVESTMENT_DOMAIN_TOOLS
from .llm.tools import TOOL_REGISTRY

logger = logging.getLogger("banorte.mcp_server")
server = Server("intellibank-domain-tools")


def _mcp_tools() -> list[types.Tool]:
    tools: list[types.Tool] = []
    for spec in INVESTMENT_DOMAIN_TOOLS:
        input_schema = copy.deepcopy(spec["input_schema"])
        input_schema.setdefault("properties", {})["user_id"] = {"type": "integer"}
        required = input_schema.setdefault("required", [])
        if "user_id" not in required:
            required.append("user_id")
        tools.append(types.Tool(
            name=spec["name"],
            description=spec["description"],
            inputSchema=input_schema,
        ))
    return tools


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return _mcp_tools()


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    args = dict(arguments or {})
    user_id = args.pop("user_id", None)
    fn = TOOL_REGISTRY.get(name) if name in INVESTMENT_DOMAIN_TOOL_NAMES else None

    if not fn:
        result = {"error": f"tool desconocida: {name}"}
    elif user_id is None:
        result = {"error": f"argumentos invalidos para {name}: falta user_id"}
    else:
        db = SessionLocal()
        try:
            result = fn(db=db, user_id=user_id, **args)
        except TypeError as exc:
            logger.exception("Argumentos invalidos para tool %s", name)
            result = {"error": f"argumentos invalidos para {name}: {exc}"}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error ejecutando tool %s", name)
            result = {"error": str(exc)}
        finally:
            db.close()

    return [types.TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False),
    )]


async def _run() -> None:
    # El transporte oficial ya trata explícitamente las diferencias de stdio
    # de Windows y fuerza UTF-8. Evitamos envolver las tuberías manualmente:
    # con ProactorEventLoop esa adaptación podía bloquear la inicialización.
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(_run())
