"""Stage: Align check -- two independently-prompted checkers review the
decomposition against goals:

  CHECKER A (scope creep)  -- is the task even about the goal's topic?
  CHECKER B (goal drift)   -- if so, does it actually move the goal's
                              stated success metric?

They are never voted or averaged, against each other or against the
doer (decompose, whose implicit stance on every task it produced is
"this belongs"). Any disagreement among the three -- A vs B, A vs doer,
B vs doer -- HALTS the task and logs the specific disagreement. The
founder resolves it; nothing is auto-fixed or auto-dropped.
"""
from __future__ import annotations

import re

from ..io import FounderIO
from ..models import Goal, Task
from ..personas import checker_a_scope_creep, checker_b_goal_drift
from ..storage import Store


def _slug(text: str) -> str:
    """Stable, run-independent key for a goal (goal ids regenerate every
    run since plan.py mints fresh ones; the goal's text does not)."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40]


def run(io: FounderIO, tasks: list[Task], goals: list[Goal], store: Store) -> tuple[list[Task], list[Task]]:
    goals_by_id = {g.id: g for g in goals}
    surviving: list[Task] = []
    halted: list[Task] = []

    print("\n=== ALIGN CHECK (CHECKER A -- scope creep, CHECKER B -- goal drift) ===")
    for t in tasks:
        goal = goals_by_id[t.goal_id]
        a = checker_a_scope_creep(t.description, goal.text)
        b = checker_b_goal_drift(t.description, goal.metric)

        voices = [
            ("decompose (doer)", "pass", "Task was included in the decomposition without objection."),
            (a.persona, a.verdict, a.reasoning),
            (b.persona, b.verdict, b.reasoning),
        ]
        distinct = {v[1] for v in voices}

        print(f"  [{t.id}] {t.description}")
        for name, verdict, reasoning in voices:
            print(f"      {name}: {verdict.upper()} -- {reasoning}")

        if len(distinct) == 1:
            t.status = "aligned"
            t.log("align_check", "unanimous_pass", "Doer, Checker A, and Checker B all agree.")
            surviving.append(t)
            continue

        # Disagreement -- either checker differs from the doer, or the two
        # checkers differ from each other. Log each checker's dissent as
        # its own audit-log entry (tagged with its own pattern) so Learn
        # can cluster root causes; the founder still resolves the task once.
        disagreement_lines = [f"{name}: {verdict.upper()} -- {reasoning}" for name, verdict, reasoning in voices]
        summary = " | ".join(disagreement_lines)
        print(f"      -> DISAGREEMENT, not unanimous. Logging as open, not auto-resolving.")

        t.status = "halted"
        t.log("align_check", "disagreement", summary)
        for persona_verdict in (a, b):
            if persona_verdict.verdict == "halt":
                full_pattern = f"{persona_verdict.pattern}:{_slug(goal.text)}"
                store.log("disagreement", persona_verdict.persona, t.id, summary, pattern=full_pattern)
        halted.append(t)

    if halted:
        print(f"\n{len(halted)} task(s) HALTED by disagreement at align-check. Founder must resolve each.")
        for t in halted:
            answer = io.ask(
                f"Task [{t.id}] '{t.description}' has an open checker disagreement (see above). "
                f"Keep it anyway (k) or drop it (d)?"
            )
            if answer.strip().lower().startswith("k"):
                t.status = "aligned"
                t.log("founder", "override_align_disagreement", "Founder kept the task despite the disagreement.")
                store.log("override", "founder", t.id, "Founder overrode align-check disagreement and kept the task.")
                surviving.append(t)
            else:
                t.status = "dropped"
                t.log("founder", "drop_task", "Founder dropped the task after align-check disagreement.")
                store.log("info", "founder", t.id, "Founder dropped the task after align-check disagreement.")

    return surviving, halted
