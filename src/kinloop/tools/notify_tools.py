"""Tools for the NotifierAgent: the escalation gatekeeper.

This is the piece that makes Kinloop "surface only when there's a real
decision to make" instead of pinging the family constantly. Routine,
already-resolved, or purely informational updates go to the activity log
only. Only genuine decisions get pushed out as a notification.
"""

from __future__ import annotations

from strands import tool

from kinloop import config
from kinloop.data_store import get_store


@tool
def send_notification(recipient: str, message: str, requires_decision: bool) -> str:
    """Send a notification to a family member. Set requires_decision=True
    only when a human genuinely needs to choose between options — routine
    status updates should NOT set this and should go to the log instead."""
    store = get_store()

    if not requires_decision:
        store.append_activity({"agent": "NotifierAgent", "summary": f"(routine, not sent) {message}"})
        return "Routine update — logged only, no notification sent."

    decision = store.add_pending_decision({"recipient": recipient, "message": message})

    if config.NOTIFY_CHANNEL == "console":
        print(f"[KINLOOP NOTIFICATION -> {recipient}] {message}")
    elif config.NOTIFY_CHANNEL == "slack" and config.SLACK_WEBHOOK_URL:
        import json
        import urllib.request

        req = urllib.request.Request(
            config.SLACK_WEBHOOK_URL,
            data=json.dumps({"text": f"*Kinloop needs a decision* ({recipient}): {message}"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    elif config.NOTIFY_CHANNEL == "ses" and config.SES_SENDER:
        import boto3

        ses = boto3.client("ses", region_name=config.AWS_REGION)
        ses.send_email(
            Source=config.SES_SENDER,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": "Kinloop needs a decision"},
                "Body": {"Text": {"Data": message}},
            },
        )

    store.append_activity({"agent": "NotifierAgent", "summary": f"Escalated to {recipient}: {message}"})
    return f"Notification sent to {recipient}, pending decision id={decision['id']}"
