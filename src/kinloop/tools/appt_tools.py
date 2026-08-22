"""Tools for the ApptAgent: appointment conflict detection across a family.

Like med_tools, the actual conflict-detection logic is a pure function so it
can be unit tested without ever calling a model.
"""

from __future__ import annotations

from datetime import datetime

from strands import tool

from kinloop.data_store import get_store


def _overlaps(a: dict, b: dict) -> bool:
    a_start, a_end = datetime.fromisoformat(a["start"]), datetime.fromisoformat(a["end"])
    b_start, b_end = datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"])
    return a_start < b_end and b_start < a_end


def compute_conflicts(appointments: list[dict]) -> list[dict]:
    """Pure function: find appointments that need the same driver/attendee
    at overlapping times, or that have nobody assigned to drive at all."""
    conflicts = []
    for i, appt in enumerate(appointments):
        if not appt.get("driver"):
            conflicts.append(
                {
                    "type": "no_driver_assigned",
                    "appointment": appt["title"],
                    "start": appt["start"],
                    "patient": appt.get("patient", "unknown"),
                }
            )
        for other in appointments[i + 1 :]:
            if appt.get("driver") and appt.get("driver") == other.get("driver") and _overlaps(appt, other):
                conflicts.append(
                    {
                        "type": "double_booked_driver",
                        "driver": appt["driver"],
                        "appointment_a": appt["title"],
                        "appointment_b": other["title"],
                        "start": appt["start"],
                    }
                )
    return conflicts


@tool
def detect_conflicts() -> list[dict]:
    """Scan all upcoming appointments for scheduling conflicts: a family
    member double-booked as a driver/attendee, or an appointment with
    nobody assigned to take the patient."""
    store = get_store()
    return compute_conflicts(store.appointments())


@tool
def propose_reassignment(conflict_description: str, candidate_family_members: list[str]) -> str:
    """Given a described conflict and the family members who are free at
    that time, propose which one should take over the appointment. This is
    a *proposal only* — ApptAgent never re-assigns automatically, it hands
    the proposal to NotifierAgent for a human to confirm."""
    if not candidate_family_members:
        return "No family member is free at that time — this needs a human decision."
    return f"Proposal: ask {candidate_family_members[0]} to cover — they have no conflicting appointment."


@tool
def log_appt_action(summary: str) -> str:
    """Record what the ApptAgent did this run."""
    get_store().append_activity({"agent": "ApptAgent", "summary": summary})
    return "logged"
