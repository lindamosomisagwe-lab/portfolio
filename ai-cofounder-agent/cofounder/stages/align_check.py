"""Stage 6: Align check -- THE SKEPTIC reviews decomposition against goals.
On a real mismatch: HALT (andon cord) and log it. Never silently fix or
drop the task -- the founder decides."""
from __future__ import annotations

from ..io import FounderIO
from ..models import Goal, Task
from ..personas import skeptic_check_task
from ..storage import Store


def run(io: FounderIO, tasks: list[Task], goals: list[Goal], store: Store) -> tuple[list[Task], list[Task]]:
    goals_by_id = {g.id: g for g in goals}
    surviving: list[Task] = []
    halted: list[Task] = []

    print("\n=== ALIGN CHECK (THE SKEPTIC) ===")
    for t in tasks:
        goal = goals_by_id[t.goal_id]
        verdict = skeptic_check_task(t.description, goal.text, goal.metric)
        print(f"  [{t.id}] {t.description}")
        print(f"      -> {verdict.verdict.upper()}: {verdict.reasoning}")

        if verdict.verdict == "halt":
            t.status = "halted"
            t.log("THE SKEPTIC", "align_check_halt", verdict.reasoning)
            store.log("halt", "THE SKEPTIC (align-checker)", t.id, verdict.reasoning)
            halted.append(t)
        else:
            t.status = "aligned"
            t.log("THE SKEPTIC", "align_check_pass", verdict.reasoning)
            surviving.append(t)

    if halted:
        print(f"\n{len(halted)} task(s) HALTED by align-check. Founder must resolve each before proceeding.")
        for t in halted:
            answer = io.ask(
                f"Task [{t.id}] '{t.description}' was flagged as not tied to any goal. "
                f"Keep it anyway (k) or drop it (d)?"
            )
            if answer.strip().lower().startswith("k"):
                t.status = "aligned"
                t.log("founder", "override_align_halt", "Founder chose to keep the task despite the halt.")
                store.log("override", "founder", t.id, "Founder overrode align-check halt and kept the task.")
                surviving.append(t)
            else:
                t.status = "dropped"
                t.log("founder", "drop_task", "Founder dropped the task after align-check halt.")
                store.log("info", "founder", t.id, "Founder dropped the task after align-check halt.")

    return surviving, halted
