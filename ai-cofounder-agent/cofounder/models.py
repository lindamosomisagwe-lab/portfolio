"""Data model for the pipeline. Plain dataclasses, JSON-serializable."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def now() -> str:
    # Microsecond precision -- Learn's avg-cycle-time metric needs real
    # deltas between timestamps, and this run completes in well under a
    # second, so second-precision would flatten everything to 0.00s.
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%H%M%S%f')}"


@dataclass
class HistoryEvent:
    at: str
    actor: str          # persona name or "founder"
    action: str
    detail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Task:
    id: str
    goal_id: str
    description: str
    status: str = "draft"          # draft | halted | queued_human | queued_ai | running | done | dropped
    owner: str | None = None        # "human" | "ai" | None
    classification: str | None = None      # "human_required" | "ai_doable" | None
    classification_reason: str = ""
    depends_on: list[str] = field(default_factory=list)
    result: str | None = None
    audit_passed: bool | None = None
    audit_notes: str = ""
    due: str | None = None
    history: list[dict] = field(default_factory=list)

    def log(self, actor: str, action: str, detail: str = "") -> None:
        self.history.append(HistoryEvent(now(), actor, action, detail).to_dict())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Goal:
    id: str
    text: str
    metric: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CheckResult:
    checker: str
    target_id: str
    verdict: str        # "pass" | "halt"
    reasoning: str
    at: str = field(default_factory=now)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AuditLogEntry:
    at: str
    kind: str            # "halt" | "disagreement" | "override" | "info" | "control"
    source: str
    subject_id: str
    message: str
    pattern: str = ""    # root-cause slug, used by Learn to cluster and to
                          # verify (in Control) whether a past rule held
    markers: list[str] = field(default_factory=list)  # structured matched
                          # markers, so Learn can reuse them without
                          # regex-parsing prose back out of the message

    def to_dict(self) -> dict:
        return asdict(self)
