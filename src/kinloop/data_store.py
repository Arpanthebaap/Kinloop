"""Data access layer for Kinloop.

Kinloop's business logic never touches a file path or a DynamoDB table
directly — it goes through this module. That keeps the same agent/tool code
working unmodified whether you're running locally against JSON fixtures
(the default, zero AWS cost) or deployed against DynamoDB in production.

Swap backends with the KINLOOP_DATA_BACKEND env var: "local" | "dynamodb".
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from kinloop import config


def _local_path(name: str) -> str:
    return os.path.join(config.LOCAL_DATA_DIR, f"{name}.json")


def _local_read(name: str) -> Any:
    path = _local_path(name)
    if not os.path.exists(path):
        return [] if name != "family" else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _local_write(name: str, data: Any) -> None:
    path = _local_path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


class Store:
    """Thin repository over family/medications/appointments/deadlines/log."""

    def __init__(self) -> None:
        self.backend = config.DATA_BACKEND
        if self.backend == "dynamodb":
            import boto3  # imported lazily so local/demo runs need no boto3 creds

            self._ddb = boto3.resource("dynamodb", region_name=config.AWS_REGION)
        else:
            self._ddb = None

    # -- generic collection access ------------------------------------
    def get_collection(self, name: str) -> list[dict]:
        if self.backend == "local":
            return _local_read(name)
        table = self._ddb.Table(f"{config.DYNAMODB_TABLE_PREFIX}_{name}")
        return table.scan().get("Items", [])

    def save_collection(self, name: str, items: list[dict]) -> None:
        if self.backend == "local":
            _local_write(name, items)
            return
        table = self._ddb.Table(f"{config.DYNAMODB_TABLE_PREFIX}_{name}")
        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)

    # -- domain-specific helpers ---------------------------------------
    def family(self) -> dict:
        return _local_read("family") if self.backend == "local" else self.get_collection("family")

    def medications(self) -> list[dict]:
        return self.get_collection("medications")

    def appointments(self) -> list[dict]:
        return self.get_collection("appointments")

    def deadlines(self) -> list[dict]:
        return self.get_collection("deadlines")

    def append_activity(self, entry: dict) -> None:
        """Append one line to the human-readable activity log."""
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), **entry}
        log = self.get_collection("activity_log")
        log.append(entry)
        self.save_collection("activity_log", log)

    def add_pending_decision(self, decision: dict) -> None:
        """Queue a decision that needs a human — this is what the
        NotifierAgent escalates and what the dashboard highlights."""
        decision = {
            "id": f"dec_{int(datetime.now(timezone.utc).timestamp())}",
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            **decision,
        }
        pending = self.get_collection("pending_decisions")
        pending.append(decision)
        self.save_collection("pending_decisions", pending)
        return decision


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store
