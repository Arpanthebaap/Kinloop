"""Dry-run mode — runs Kinloop's real decision logic without calling Bedrock.

This exists for one honest reason: AWS blocks Bedrock calls on brand-new
accounts during identity/billing verification, sometimes for days. That
restriction has nothing to do with whether Kinloop works — the tool logic
underneath every agent (refill status, conflict detection, deadline
urgency, and the escalation thresholds NotifierAgent uses) is plain,
tested Python with no LLM involved. This module runs that same logic
directly and narrates it the way the agents would, so development,
testing, and even a demo recording aren't blocked on AWS's account review.

IMPORTANT — this is NOT a substitute for the real thing and should never be
presented as one. Every line of output below is prefixed [DRY RUN] and the
demo video / text description should say plainly that this mode exists and
why. What it proves: the underlying logic is real, tested, and correct.
What it does NOT prove: the agents' natural-language reasoning, which only
happens through an actual Bedrock call (see main.py without --dry-run).

Usage:
    python -m kinloop.main --dry-run
"""

from __future__ import annotations

from datetime import date

from kinloop.data_store import get_store
from kinloop.tools.appt_tools import compute_conflicts
from kinloop.tools.med_tools import compute_refill_status
from kinloop.tools.paperwork_tools import compute_deadline_status

TAG = "[DRY RUN — no Bedrock call made]"


def run_dry_run_check() -> str:
    """Mirror what Supervisor -> specialists -> NotifierAgent would do,
    using the real deterministic logic directly instead of through an
    LLM tool-calling loop. Returns a human-readable summary and writes
    the same activity_log / pending_decisions entries a real run would."""
    store = get_store()
    lines = [f"{TAG} Running Kinloop's daily check-in logic directly (Bedrock unavailable).\n"]

    # --- MedAgent equivalent ---
    med_results = [compute_refill_status(m) for m in store.medications()]
    overdue = [m for m in med_results if m["status"] == "overdue"]
    warning = [m for m in med_results if m["status"] == "warning"]
    lines.append(f"MedAgent: checked {len(med_results)} medications.")
    for m in overdue:
        lines.append(f"  - OVERDUE: {m['name']} ({m['person']}) — refill request would be drafted automatically.")
        store.append_activity({"agent": "MedAgent", "summary": f"{TAG} {m['name']} overdue, refill drafted"})
    for m in warning:
        lines.append(f"  - running low: {m['name']} ({m['days_supply_remaining']} days left) — noted, not yet escalated.")

    # --- ApptAgent equivalent ---
    conflicts = compute_conflicts(store.appointments())
    lines.append(f"\nApptAgent: checked appointments, found {len(conflicts)} conflict(s).")
    for c in conflicts:
        if c["type"] == "double_booked_driver":
            lines.append(f"  - {c['driver']} double-booked: {c['appointment_a']} / {c['appointment_b']} at {c['start']}")
        else:
            lines.append(f"  - No driver assigned: {c['appointment']} at {c['start']}")
        store.append_activity({"agent": "ApptAgent", "summary": f"{TAG} conflict: {c}"})

    # --- PaperworkAgent equivalent ---
    deadlines = [compute_deadline_status(d, today=date.today()) for d in store.deadlines()]
    urgent = [d for d in deadlines if d["status"] in ("urgent", "missed")]
    lines.append(f"\nPaperworkAgent: checked {len(deadlines)} deadlines.")
    for d in urgent:
        lines.append(f"  - {d['status'].upper()}: {d['name']}, due {d['due_date']}, missing {d['missing_fields']}")
        store.append_activity({"agent": "PaperworkAgent", "summary": f"{TAG} {d['name']} {d['status']}"})

    # --- NotifierAgent equivalent: same escalation policy, applied directly ---
    lines.append("\nNotifierAgent: applying escalation policy —")
    escalations = []
    for c in conflicts:
        msg = (
            f"Scheduling conflict needs a decision: {c}"
        )
        escalations.append(msg)
        store.add_pending_decision({"recipient": "family", "message": f"{TAG} {msg}"})
    for d in urgent:
        msg = f"Paperwork needs attention: {d['name']} is {d['status']}, missing {d['missing_fields']}."
        escalations.append(msg)
        store.add_pending_decision({"recipient": "family", "message": f"{TAG} {msg}"})

    if escalations:
        lines.append(f"  {len(escalations)} item(s) escalated (see pending_decisions).")
        for e in escalations:
            lines.append(f"  - {e}")
    else:
        lines.append("  Nothing needed a human today — everything was routine.")

    store.append_activity({"agent": "NotifierAgent", "summary": f"{TAG} escalated {len(escalations)} item(s)"})

    lines.append(
        f"\n{TAG} This ran the real tool logic with no LLM call. "
        "The agents' natural-language reasoning (drafting messages, phrasing "
        "notifications, deciding between ambiguous cases) only happens via "
        "Bedrock — run without --dry-run once AWS account access is confirmed."
    )
    return "\n".join(lines)
