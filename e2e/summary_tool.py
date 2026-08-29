from __future__ import annotations

import asyncio
import json
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from tools.summary.summary import ConversationSummaryTool

SUMMARY_TOOL_ERROR_PREFIX = "summary_tool_error: "


def summarize_case_result(result: dict[str, Any]) -> str:
    messages = build_summary_messages(result)
    try:
        return run_summary_tool(messages)
    except Exception as exc:
        return f"{SUMMARY_TOOL_ERROR_PREFIX}{type(exc).__name__}: {exc}"


def build_summary_messages(result: dict[str, Any]) -> list[ModelMessage]:
    return [
        ModelRequest(parts=[UserPromptPart(content=summary_prompt(result))]),
        ModelResponse(parts=[TextPart(content=str(result.get("final_response") or ""))]),
    ]


def run_summary_tool(messages: list[ModelMessage]) -> str:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(call_summary_tool(messages))
    raise RuntimeError("summary tool cannot be run from an active event loop")


async def call_summary_tool(messages: list[ModelMessage]) -> str:
    tool = ConversationSummaryTool(
        agent=Agent("google-vertex:gemini-2.5-flash"),
        scrubber=E2ESummaryScrubber(),
        audit_store=E2ESummaryAuditStore(),
    )
    return await tool.run(summary_tool_messages(messages))


def summary_prompt(result: dict[str, Any]) -> str:
    return (
        "Summarize this e2e test case result for the operator. Include the case identity, "
        "expected outcome, actual outcome, classification, pass/fail status, assertion errors, "
        "death-certificate tool result, skipped turns, and a concise explanation of what happened. "
        "Preserve any existing summary fields as source data; do not replace them.\n\n"
        f"{json.dumps(summary_payload(result), indent=2, ensure_ascii=False, default=str)}"
    )


def summary_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "case": result.get("case"),
        "country": result.get("country"),
        "kind": result.get("kind"),
        "case_id": result.get("case_id"),
        "expected_outcome": result.get("expected_outcome"),
        "actual_outcome": result.get("actual_outcome"),
        "classification": result.get("classification"),
        "verdict_source": result.get("verdict_source"),
        "passed": result.get("passed"),
        "errors": result.get("errors", []),
        "skipped_turns": result.get("skipped_turns", []),
        "tool_result": result.get("tool_result"),
        "turns": [compact_turn(turn) for turn in result.get("turns", [])],
    }


def compact_turn(turn: dict[str, Any]) -> dict[str, Any]:
    response_json = turn.get("response_json")
    response_body = None
    if isinstance(response_json, dict):
        response_body = response_json.get("response")
    return {
        "label": turn.get("label"),
        "status_code": turn.get("status_code"),
        "latency_seconds": turn.get("latency_seconds"),
        "response": response_body if response_body is not None else turn.get("response_text"),
    }


def summary_tool_messages(messages: list[ModelMessage]) -> list[SummaryToolMessage]:
    return [SummaryToolMessage(message) for message in messages]


class SummaryToolMessage:
    def __init__(self, message: ModelMessage) -> None:
        self.message = message

    def model_dump_json(self, *, exclude_none: bool = False, **kwargs: Any) -> str:
        dumped = ModelMessagesTypeAdapter.dump_python([self.message], exclude_none=exclude_none)[0]
        return json.dumps(dumped, ensure_ascii=False, default=str)


class E2ESummaryScrubber:
    def scrub(self, transcript: str, *, audit_store: Any) -> str:
        return transcript


class E2ESummaryAuditStore:
    pass
