"""Tools for the PaperworkAgent: recurring deadlines (insurance
recertification, benefit renewals, etc.) and document field extraction.
"""

from __future__ import annotations

from datetime import date, datetime

from strands import tool

from kinloop.data_store import get_store

DEADLINE_WARNING_DAYS = 14


def compute_deadline_status(deadline: dict, today: date | None = None) -> dict:
    """Pure function: how urgent is this paperwork deadline."""
    today = today or date.today()
    due = datetime.fromisoformat(deadline["due_date"]).date()
    days_remaining = (due - today).days
    if days_remaining < 0:
        status = "missed"
    elif days_remaining <= DEADLINE_WARNING_DAYS:
        status = "urgent"
    else:
        status = "ok"
    return {
        "name": deadline["name"],
        "due_date": deadline["due_date"],
        "days_remaining": days_remaining,
        "status": status,
        "missing_fields": deadline.get("missing_fields", []),
    }


@tool
def check_deadline() -> list[dict]:
    """Check every tracked paperwork/benefit deadline and report which are
    fine, urgent (due soon), or already missed."""
    store = get_store()
    return [compute_deadline_status(d) for d in store.deadlines()]


@tool
def extract_form_fields(document_text: str, required_fields: list[str]) -> dict:
    """Given the raw text of an uploaded document and a list of required
    field names, identify which required fields are present vs. missing.

    NOTE: this is a lightweight keyword-based extraction for the demo. A
    production build would route this through Amazon Bedrock's document
    understanding / a Textract call for real OCR + field extraction."""
    text_lower = document_text.lower()
    present = [f for f in required_fields if f.lower() in text_lower]
    missing = [f for f in required_fields if f not in present]
    return {"present_fields": present, "missing_fields": missing}


@tool
def log_paperwork_action(summary: str) -> str:
    """Record what the PaperworkAgent did this run."""
    get_store().append_activity({"agent": "PaperworkAgent", "summary": summary})
    return "logged"
