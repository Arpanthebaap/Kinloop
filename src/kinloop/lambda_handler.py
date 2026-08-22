"""AWS Lambda entry point.

This is what EventBridge Scheduler invokes once a day in production. It's
deliberately a thin wrapper around the same `run_daily_check` used locally —
there is no separate "production" code path to keep in sync.

Deploy target: AWS Lambda (see /deploy/template.yaml). Kept off AgentCore
Runtime on purpose for the always-on deployment — see docs/text_description.md
for the cost reasoning. An optional AgentCore-based entrypoint is provided
separately in /deploy/agentcore/app.py for a one-time demo deployment.
"""

import json

from kinloop.agents.supervisor import run_daily_check


def handler(event, context):
    """event = {} for the normal scheduled trigger, or
    {"note": "..."} to pass extra context (e.g. for manual test invokes)."""
    note = ""
    if isinstance(event, dict):
        note = event.get("note", "")

    summary = run_daily_check(context_note=note)

    return {
        "statusCode": 200,
        "body": json.dumps({"summary": summary}),
    }
