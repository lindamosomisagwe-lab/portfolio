"""Data model for the pipeline. Plain dataclasses, JSON-serializable."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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
    kind: str            # "halt" | "disagreement" | "override" | "info"
    source: str
    subject_id: str
    message: str

    def to_dict(self) -> dict:
        return asdict(self)
