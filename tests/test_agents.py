"""Unit tests for Kinloop's deterministic business logic.

These test the pure Python functions behind each tool — no Bedrock/LLM
calls, no AWS credentials needed, no cost. Run with:

    pytest tests/
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kinloop.tools.appt_tools import compute_conflicts
from kinloop.tools.med_tools import compute_refill_status
from kinloop.tools.paperwork_tools import compute_deadline_status


class TestRefillStatus:
    def test_overdue_when_zero_days_left(self):
        med = {"name": "X", "person": "P", "days_supply_remaining": 0}
        assert compute_refill_status(med)["status"] == "overdue"

    def test_warning_within_threshold(self):
        med = {"name": "X", "person": "P", "days_supply_remaining": 3}
        assert compute_refill_status(med)["status"] == "warning"

    def test_ok_when_plenty_remaining(self):
        med = {"name": "X", "person": "P", "days_supply_remaining": 30}
        assert compute_refill_status(med)["status"] == "ok"


class TestConflictDetection:
    def test_double_booked_driver_detected(self):
        appts = [
            {"title": "A", "start": "2026-01-01T09:00:00", "end": "2026-01-01T10:00:00", "driver": "Sam"},
            {"title": "B", "start": "2026-01-01T09:30:00", "end": "2026-01-01T10:30:00", "driver": "Sam"},
        ]
        conflicts = compute_conflicts(appts)
        types = [c["type"] for c in conflicts]
        assert "double_booked_driver" in types

    def test_no_conflict_for_different_drivers_same_time(self):
        appts = [
            {"title": "A", "start": "2026-01-01T09:00:00", "end": "2026-01-01T10:00:00", "driver": "Sam"},
            {"title": "B", "start": "2026-01-01T09:30:00", "end": "2026-01-01T10:30:00", "driver": "Alex"},
        ]
        conflicts = compute_conflicts(appts)
        assert not any(c["type"] == "double_booked_driver" for c in conflicts)

    def test_missing_driver_flagged(self):
        appts = [{"title": "A", "start": "2026-01-01T09:00:00", "end": "2026-01-01T10:00:00", "driver": None}]
        conflicts = compute_conflicts(appts)
        assert any(c["type"] == "no_driver_assigned" for c in conflicts)

    def test_non_overlapping_same_driver_is_fine(self):
        appts = [
            {"title": "A", "start": "2026-01-01T09:00:00", "end": "2026-01-01T10:00:00", "driver": "Sam"},
            {"title": "B", "start": "2026-01-01T11:00:00", "end": "2026-01-01T12:00:00", "driver": "Sam"},
        ]
        conflicts = compute_conflicts(appts)
        assert not any(c["type"] == "double_booked_driver" for c in conflicts)


class TestDeadlineStatus:
    def test_missed_when_past_due(self):
        deadline = {"name": "X", "due_date": "2020-01-01"}
        result = compute_deadline_status(deadline, today=date(2026, 1, 1))
        assert result["status"] == "missed"

    def test_urgent_within_warning_window(self):
        deadline = {"name": "X", "due_date": "2026-01-10"}
        result = compute_deadline_status(deadline, today=date(2026, 1, 1))
        assert result["status"] == "urgent"

    def test_ok_when_far_out(self):
        deadline = {"name": "X", "due_date": "2026-06-01"}
        result = compute_deadline_status(deadline, today=date(2026, 1, 1))
        assert result["status"] == "ok"
