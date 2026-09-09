"""Persistent JSON stores: goal-context, task-board, checker-rules, audit-log."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import AuditLogEntry, now

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _path(name: str) -> Path:
    return DATA_DIR / f"{name}.json"


def _load(name: str, default: Any) -> Any:
    p = _path(name)
    if not p.exists():
        return default
    with p.open() as f:
        return json.load(f)


def _save(name: str, data: Any) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    p = _path(name)
    with p.open("w") as f:
        json.dump(data, f, indent=2, default=str)


class Store:
    """Thin wrapper over the four persistent stores. Reload/save per call —
    this is a single-process CLI prototype, not a concurrent service."""

    # -- goal-context ---------------------------------------------------
    def load_goal_context(self) -> dict:
        return _load("goal-context", {})

    def save_goal_context(self, ctx: dict) -> None:
        _save("goal-context", ctx)

    # -- task-board -------------------------------------------------------
    def load_task_board(self) -> dict:
        return _load("task-board", {})

    def save_task_board(self, board: dict) -> None:
        _save("task-board", board)

    def upsert_task(self, task_dict: dict) -> None:
        board = self.load_task_board()
        existing = board.get(task_dict["id"])
        if existing and existing.get("owner") == "human" and task_dict.get("owner") != "human":
            # NEVER silently overwrite a human's existing task ownership.
            raise RuntimeError(
                f"refusing to overwrite human-owned task {task_dict['id']} without explicit reassignment"
            )
        board[task_dict["id"]] = task_dict
        self.save_task_board(board)

    # -- checker-rules ----------------------------------------------------
    def load_rules(self) -> list[dict]:
        return _load("checker-rules", [])

    def save_rules(self, rules: list[dict]) -> None:
        _save("checker-rules", rules)

    def add_rule(self, rule_text: str, source: str, pattern: str = "", marker_words: list[str] | None = None) -> None:
        """`pattern` and `marker_words` make the rule machine-actionable:
        Learn's Control phase matches on `pattern` to check whether a rule
        held; classify.py reads `marker_words` back out to actually widen
        THE CLASSIFIER's marker set on the next run."""
        rules = self.load_rules()
        rules.append({
            "rule": rule_text,
            "source": source,
            "pattern": pattern,
            "marker_words": marker_words or [],
            "added_at": now(),
        })
        self.save_rules(rules)

    # -- audit-log ----------------------------------------------------------
    def load_audit_log(self) -> list[dict]:
        return _load("audit-log", [])

    def append_audit_log(self, entry: AuditLogEntry) -> None:
        log = self.load_audit_log()
        log.append(entry.to_dict())
        _save("audit-log", log)

    def log(self, kind: str, source: str, subject_id: str, message: str,
            pattern: str = "", markers: list[str] | None = None) -> None:
        self.append_audit_log(AuditLogEntry(now(), kind, source, subject_id, message, pattern, markers or []))
