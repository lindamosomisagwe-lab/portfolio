"""Orchestrates the pipeline, stage by stage, enforcing both checker halts
along the way. Idea validation/analysis is out of scope here -- the
founder brings an idea they've already decided to act on, and the
pipeline picks up at planning."""
from __future__ import annotations

from .io import FounderIO
from .models import now
from .storage import DATA_DIR, Store
from .stages import align_check, audit, classify, decompose, execute, learn, plan, route, routing_check


def run(io: FounderIO, idea_text: str, store: Store) -> None:
    run_started_at = now()
    print("=== IDEA INTAKE ===")
    print(idea_text)
    store.log("info", "founder", "idea", "Idea submitted; proceeding straight to planning.")

    # Stage: plan and goals
    plan_context, goals = plan.run(io, idea_text)
    store.save_goal_context({
        "idea": idea_text,
        "plan": plan_context,
        "goals": [g.to_dict() for g in goals],
    })

    # Stage: decompose
    tasks = decompose.run(goals)

    # Stage: align check (andon cord)
    surviving, align_halted = align_check.run(io, tasks, goals, store)

    # Stage: classify
    classified = classify.run(surviving, store)

    # Stage: routing check (second, differently-prompted checker)
    routed_tasks, routing_disagreements = routing_check.run(io, classified, store)

    # Stage: route into human queue / AI queue
    human_tasks, ai_tasks = route.run(routed_tasks, store)

    # Stage: execute AI-doable tasks in parallel via the shared executor
    ai_tasks = execute.run(ai_tasks)

    # Stage: audit before marking anything done
    ai_tasks = audit.run(ai_tasks, store)

    # Stage: learn + check-in (real DMAIC, scoped to this cycle's timestamp)
    learn.run(store, run_started_at, tasks, goals, ai_tasks)

    print("\n=== RUN SUMMARY ===")
    print(f"Human queue: {len(human_tasks)} task(s) awaiting a human.")
    print(f"AI-executed: {sum(1 for t in ai_tasks if t.status == 'done')} done, "
          f"{sum(1 for t in ai_tasks if t.status == 'halted')} halted at audit.")
    print(f"Align-check halts resolved: {len(align_halted)}")
    print(f"Routing-check disagreements resolved: {len(routing_disagreements)}")
    print(f"Persisted state under: {DATA_DIR}")
