"""Stage 9: Route -- human-required tasks go into the human queue.
AI-doable tasks are queued for parallel execution. Never silently
overwrite a human's existing task ownership (storage.Store enforces
this on upsert)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..models import Task
from ..storage import Store


def run(tasks: list[Task], store: Store) -> tuple[list[Task], list[Task]]:
    human_tasks = [t for t in tasks if t.classification == "human_required"]
    ai_tasks = [t for t in tasks if t.classification == "ai_doable"]

    now = datetime.now(timezone.utc)
    for i, t in enumerate(human_tasks):
        t.owner = "human"
        t.status = "queued_human"
        # First human task simulated as already overdue, to give the Learn
        # stage's reminder check something real to find in this sample run.
        t.due = (now - timedelta(days=3) if i == 0 else now + timedelta(days=7)).isoformat(timespec="seconds")
        t.log("route", "queued_human", f"due {t.due}")
        store.upsert_task(t.to_dict())

    for t in ai_tasks:
        t.owner = "ai"
        t.status = "queued_ai"
        t.log("route", "queued_ai", "dispatched to AI executor pool")
        store.upsert_task(t.to_dict())

    print("\n=== ROUTE ===")
    print(f"Human queue ({len(human_tasks)}):")
    for t in human_tasks:
        print(f"  [{t.id}] {t.description}  (due {t.due})")
    print(f"AI queue ({len(ai_tasks)}), to run in parallel where independent:")
    for t in ai_tasks:
        print(f"  [{t.id}] {t.description}")

    return human_tasks, ai_tasks
