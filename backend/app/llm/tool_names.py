"""Helpers for normalizing tool names emitted by the LLM."""

SENSITIVE_TOOLS = {
    "apply_credit_plan",
    "confirm_investment",
    "schedule_payment",
    "confirm_insurance_policy",
    "file_insurance_claim",
    "contribute_to_goal",
    "execute_transfer",
}


def normalize_tool_name(name: str) -> str:
    return name.removeprefix("functions.")
