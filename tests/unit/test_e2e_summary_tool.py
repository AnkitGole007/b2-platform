from __future__ import annotations

from pydantic_ai.messages import ModelRequest, ModelResponse

from e2e import summary_tool
from tools.summary.summary import ConversationSummaryTool


def test_build_summary_messages_keeps_existing_tool_summary_context() -> None:
    result = {
        "case": "example/real/case_001",
        "country": "example",
        "kind": "real",
        "case_id": "case_001",
        "expected_outcome": "accept",
        "actual_outcome": "reject",
        "classification": "FN",
        "verdict_source": "tool_result",
        "passed": False,
        "errors": ["actual outcome 'reject' != expected 'accept'"],
        "tool_result": {
            "accepted": False,
            "summary": "Original death certificate verification summary.",
        },
        "turns": [
            {
                "label": "media",
                "status_code": 200,
                "latency_seconds": 1.25,
                "response_json": {"response": "The certificate was rejected."},
            }
        ],
        "final_response": "The certificate was rejected.",
    }

    messages = summary_tool.build_summary_messages(result)

    assert len(messages) == 2
    assert isinstance(messages[0], ModelRequest)
    assert isinstance(messages[1], ModelResponse)
    request_content = messages[0].parts[0].content
    response_content = messages[1].parts[0].content
    assert "example/real/case_001" in request_content
    assert '"classification": "FN"' in request_content
    assert '"summary": "Original death certificate verification summary."' in request_content
    assert response_content == "The certificate was rejected."


def test_summarize_case_result_returns_summary_tool_response(monkeypatch) -> None:
    seen = {}

    async def fake_call(messages):
        seen["messages"] = messages
        return "case summary"

    monkeypatch.setattr(summary_tool, "call_summary_tool", fake_call)

    result = {
        "case": "example/real/case_001",
        "final_response": "accepted",
    }

    assert summary_tool.summarize_case_result(result) == "case summary"
    assert seen["messages"][1].parts[0].content == "accepted"


def test_summarize_case_result_records_summary_tool_errors(monkeypatch) -> None:
    async def fake_call(messages):
        raise ValueError("boom")

    monkeypatch.setattr(summary_tool, "call_summary_tool", fake_call)

    response = summary_tool.summarize_case_result({"case": "example/real/case_001"})

    assert response == "summary_tool_error: ValueError: boom"


def test_summary_tool_messages_support_conversation_summary_transcript_builder() -> None:
    messages = summary_tool.build_summary_messages(
        {
            "case": "example/real/case_001",
            "classification": "TP",
            "final_response": "verification passed",
        }
    )

    transcript = ConversationSummaryTool._build_transcript(
        object(),
        summary_tool.summary_tool_messages(messages),
    )

    assert "example/real/case_001" in transcript
    assert "verification passed" in transcript
