"""Orchestrates the full pipeline, stage by stage, enforcing the founder
checkpoint and both checker halts along the way."""
from __future__ import annotations

from .io import FounderIO
from .storage import DATA_DIR, Store
from .stages import align_check, audit, classify, decompose, execute, learn, plan, route, routing_check, validate


def run(io: FounderIO, idea_text: str, store: Store) -> None:
    print("=== IDEA INTAKE ===")
    print(idea_text)

    # Stage 2/3: validate, then a real founder checkpoint. Nothing proceeds
    # without an explicit approve.
    while True:
        validate.run(idea_text)
        decision = io.ask(
            "Founder checkpoint -- approve and proceed (a), request more analysis (m), or kill the idea (k)?"
        )
        d = decision.strip().lower()
        if d.startswith("a"):
            store.log("info", "founder", "idea", "Founder approved the idea after validation.")
            break
        if d.startswith("m"):
            focus = io.ask("What should the next pass of analysis dig into specifically?")
            idea_text = f"{idea_text}\n\n[Founder requested deeper analysis on: {focus}]"
            store.log("info", "founder", "idea", f"Founder requested more analysis: {focus}")
            continue
        if d.startswith("k"):
            print("\nIdea killed by founder at the validation checkpoint. Pipeline stops here.")
            store.log("info", "founder", "idea", "Founder killed the idea at the validation checkpoint.")
            return
        print("Please answer a, m, or k.")

    # Stage 4: plan and goals
    plan_context, goals = plan.run(io, idea_text)
    store.save_goal_context({
        "idea": idea_text,
        "plan": plan_context,
        "goals": [g.to_dict() for g in goals],
    })

    # Stage 5: decompose
    tasks = decompose.run(goals)

    # Stage 6: align check (andon cord)
    surviving, align_halted = align_check.run(io, tasks, goals, store)

    # Stage 7: classify
    classified = classify.run(surviving)

    # Stage 8: routing check (second, differently-prompted checker)
    routed_tasks, routing_disagreements = routing_check.run(io, classified, store)

    # Stage 9: route into human queue / AI queue
    human_tasks, ai_tasks = route.run(routed_tasks, store)

    # Stage 9b: execute AI-doable tasks in parallel via the shared executor
    ai_tasks = execute.run(ai_tasks)

    # Stage 10: audit before marking anything done
    ai_tasks = audit.run(ai_tasks, store)

    # Stage 11: learn + check-in
    learn.run(store, align_halted, routing_disagreements, human_tasks)

    print("\n=== RUN SUMMARY ===")
    print(f"Human queue: {len(human_tasks)} task(s) awaiting a human.")
    print(f"AI-executed: {sum(1 for t in ai_tasks if t.status == 'done')} done, "
          f"{sum(1 for t in ai_tasks if t.status == 'halted')} halted at audit.")
    print(f"Align-check halts resolved: {len(align_halted)}")
    print(f"Routing-check disagreements resolved: {len(routing_disagreements)}")
    print(f"Persisted state under: {DATA_DIR}")
