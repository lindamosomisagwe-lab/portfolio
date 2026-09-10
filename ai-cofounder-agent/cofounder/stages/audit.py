"""Stage 10: Audit -- check each AI-executed task's actual output against
what was asked before marking it done. No task is marked done without
this step."""
from __future__ import annotations

from ..models import Task
from ..personas import auditor_review
from ..storage import Store


def run(ai_tasks: list[Task], store: Store) -> list[Task]:
    print("\n=== AUDIT (THE AUDITOR) ===")
    for t in ai_tasks:
        verdict = auditor_review(t.description, t.result or "")
        t.audit_passed = verdict.verdict == "pass"
        t.audit_notes = verdict.reasoning
        if verdict.verdict == "pass":
            t.status = "done"
            t.log("THE AUDITOR", "audit_pass", verdict.reasoning)
        else:
            t.status = "halted"
            t.log("THE AUDITOR", "audit_halt", verdict.reasoning)
            store.log("halt", "THE AUDITOR", t.id, verdict.reasoning)
        store.upsert_task(t.to_dict())
        print(f"  [{t.id}] {t.description}\n      -> {verdict.verdict.upper()}: {verdict.reasoning}")

    return ai_tasks
