"""Tools for the MedAgent: medication refill tracking.

The actual "is this refill overdue" logic is a plain Python function
(`compute_refill_status`) with no LLM involved — it's cheap, deterministic,
and unit-testable on its own (see tests/test_agents.py). The @tool wrapper
just exposes it to the agent loop.
"""

from __future__ import annotations

from datetime import date, datetime

from strands import tool

from kinloop.data_store import get_store

REFILL_WARNING_DAYS = 5  # flag a refill once it's this close to running out


def compute_refill_status(med: dict, today: date | None = None) -> dict:
    """Pure function: given one medication record, decide its refill status.

    med = {
        "name": str, "person": str, "days_supply_remaining": int,
        "prescriber": str, "pharmacy": str
    }
    Returns a dict with a `status` of "ok" | "warning" | "overdue".
    """
    days_left = med.get("days_supply_remaining", 0)
    if days_left <= 0:
        status = "overdue"
    elif days_left <= REFILL_WARNING_DAYS:
        status = "warning"
    else:
        status = "ok"
    return {
        "name": med["name"],
        "person": med["person"],
        "days_supply_remaining": days_left,
        "status": status,
        "pharmacy": med.get("pharmacy", "unknown pharmacy"),
        "prescriber": med.get("prescriber", "unknown prescriber"),
    }


@tool
def check_refill_status() -> list[dict]:
    """Check every tracked medication and report which ones are ok, running
    low (warning), or already overdue for a refill."""
    store = get_store()
    meds = store.medications()
    return [compute_refill_status(m) for m in meds]


@tool
def draft_refill_message(medication_name: str, person: str, pharmacy: str) -> str:
    """Draft a short refill-request message for a specific medication that
    a family member can send to the pharmacy (or that gets auto-sent, in a
    production deployment, via a pharmacy API/SES email)."""
    return (
        f"Hello, this is a refill request for {person}'s prescription of "
        f"{medication_name}. Please let us know if anything else is needed "
        f"to process this at {pharmacy}. Thank you."
    )


@tool
def log_med_action(summary: str) -> str:
    """Record what the MedAgent did this run, for the activity log the
    dashboard shows."""
    get_store().append_activity({"agent": "MedAgent", "summary": summary})
    return "logged"
