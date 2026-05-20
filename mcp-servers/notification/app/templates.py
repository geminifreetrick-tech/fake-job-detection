"""Minimal mustache-ish templates for notification bodies. Pure-Python, no jinja."""
from __future__ import annotations

import re
from typing import Any

_PLACEHOLDER = re.compile(r"\{\{\s*([\w\.]+)\s*\}\}")


def _lookup(ctx: dict, dotted: str) -> str:
    cur: Any = ctx
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return ""
    if cur is None:
        return ""
    return str(cur)


def render(template: str, ctx: dict) -> str:
    return _PLACEHOLDER.sub(lambda m: _lookup(ctx, m.group(1)), template)


TEMPLATES: dict[str, dict[str, str]] = {
    "fraud_detected": {
        "subject": "[Fake-Job Detection] High-risk job posting detected",
        "body": (
            "Hi {{user.email}},\n\n"
            "We just analysed a job posting on your behalf and flagged it as likely FRAUD "
            "(score {{prediction.score}}).\n\n"
            "Top reasons:\n{{explanations_text}}\n\n"
            "View the full report: {{report_url}}\n\n"
            "Stay safe — Fake-Job Detection"
        ),
    },
    "report_submitted": {
        "subject": "[Fake-Job Detection] Thanks for your report",
        "body": (
            "Hi {{user.email}},\n\n"
            "Thanks for submitting a scam report (\"{{report.title}}\"). "
            "Our review team has been notified.\n\n"
            "Reference id: {{report.id}}\n"
        ),
    },
    "report_status_changed": {
        "subject": "[Fake-Job Detection] Report status updated",
        "body": (
            "Hi {{user.email}},\n\n"
            "Your report \"{{report.title}}\" is now marked as: {{report.status}}.\n"
            "Admin notes: {{report.admin_notes}}\n"
        ),
    },
}


def get(name: str) -> dict[str, str]:
    return TEMPLATES.get(name, {"subject": "Notification", "body": "{{message}}"})
