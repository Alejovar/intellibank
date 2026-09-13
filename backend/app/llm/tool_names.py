"""Helpers for normalizing tool names emitted by the LLM."""


def normalize_tool_name(name: str) -> str:
    return name.removeprefix("functions.")
