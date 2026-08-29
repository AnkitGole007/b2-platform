from __future__ import annotations

from e2e.reports import render_markdown


def test_render_markdown_includes_summary_tool_response_column() -> None:
    markdown = render_markdown(
        {
            "base_url": "http://testserver",
            "total": 1,
            "passed": 0,
            "failed": 1,
            "stats": {
                "overall": {
                    "total": 1,
                    "classified": 1,
                    "accuracy": 0.0,
                    "false_positives": 0,
                    "false_negatives": 1,
                    "unknown": 0,
                },
                "by_country": {},
            },
            "results": [
                {
                    "case": "example/real/case_001",
                    "passed": False,
                    "expected_outcome": "accept",
                    "actual_outcome": "reject",
                    "classification": "FN",
                    "final_response": "Rejected.",
                    "summary_tool_response": "Line one\nLine | two",
                    "errors": ["actual outcome 'reject' != expected 'accept'"],
                }
            ],
        }
    )

    assert (
        "| Case | Result | Expected | Actual | Class | Final Response Chars | "
        "Summary Tool Response | Errors |"
    ) in markdown
    assert (
        "| `example/real/case_001` | FAIL | accept | reject | FN | 9 | "
        "Line one<br>Line \\| two | actual outcome 'reject' != expected 'accept' |"
    ) in markdown


def test_render_markdown_handles_missing_summary_tool_response() -> None:
    markdown = render_markdown(
        {
            "base_url": "http://testserver",
            "total": 1,
            "passed": 1,
            "failed": 0,
            "stats": {
                "overall": {
                    "total": 1,
                    "classified": 1,
                    "accuracy": 1.0,
                    "false_positives": 0,
                    "false_negatives": 0,
                    "unknown": 0,
                },
                "by_country": {},
            },
            "results": [
                {
                    "case": "example/real/case_001",
                    "passed": True,
                    "expected_outcome": "accept",
                    "actual_outcome": "accept",
                    "classification": "TP",
                    "final_response": "Accepted.",
                    "errors": [],
                }
            ],
        }
    )

    assert "| `example/real/case_001` | PASS | accept | accept | TP | 9 |  |  |" in markdown
