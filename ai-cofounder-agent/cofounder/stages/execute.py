"""Stage 9b: Execute -- AI-doable tasks fan out and run in parallel where
independent. Every task goes through the exact same executor (THE DOER);
nothing here is special-cased per task."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from ..models import Task
from ..personas import doer_execute


def run(ai_tasks: list[Task]) -> list[Task]:
    print("\n=== EXECUTE (THE DOER, running independent tasks in parallel) ===")
    if not ai_tasks:
        return ai_tasks

    with ThreadPoolExecutor(max_workers=min(4, len(ai_tasks))) as pool:
        futures = {t.id: pool.submit(doer_execute, t.description) for t in ai_tasks}
        for t in ai_tasks:
            t.result = futures[t.id].result()
            t.status = "executed"
            t.log("THE DOER", "executed", "produced draft output")

    for t in ai_tasks:
        print(f"\n  [{t.id}] {t.description}\n  --- output ---\n{t.result}\n  --------------")

    return ai_tasks
