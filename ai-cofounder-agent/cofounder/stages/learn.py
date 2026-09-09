"""Stage: Learn and check-in -- real DMAIC, not a vague periodic review.

Define  -- name the numbers this cycle tracks.
Measure -- compute them from task-board + audit-log, scoped to this cycle.
Analyze -- for every halt/override this cycle, state the specific reason
           the checkers disagreed, clustered into root causes.
Improve -- write one concrete, machine-readable rule per NEW root cause.
Control -- check every rule that existed BEFORE this cycle: did its root
           cause recur this cycle anyway? If so, log it as still open --
           never mark it resolved just because a rule was written.

Separately: scan the whole human queue (not just this cycle's tasks) for
stalled work and generate founder reminders.
"""
from __future__ import annotations

from datetime import datetime, timezone

from ..models import Goal, Task
from ..storage import Store


def run(
    store: Store,
    run_started_at: str,
    all_tasks: list[Task],
    goals: list[Goal],
    ai_tasks: list[Task],
) -> dict:
    goals_by_id = {g.id: g for g in goals}
    task_by_id = {t.id: t for t in all_tasks}

    # Snapshot BEFORE this cycle's Improve step writes anything -- Control
    # needs to know which rules already existed going into this cycle.
    existing_rules = store.load_rules()
    existing_patterns = {r["pattern"]: r for r in existing_rules if r.get("pattern")}

    # ------------------------------------------------------------------ D
    print("\n=== LEARN / CHECK-IN (DMAIC) ===")
    print("-- DEFINE --")
    print("Tracking this cycle: halt rate, override rate, avg AI-task cycle "
          "time, count of stalled human tasks.")

    # ------------------------------------------------------------------ M
    print("\n-- MEASURE --")
    audit_log = store.load_audit_log()
    this_cycle_log = [e for e in audit_log if e["at"] >= run_started_at]
    disagreements_this_cycle = [e for e in this_cycle_log if e["kind"] == "disagreement"]
    overrides_this_cycle = [e for e in this_cycle_log if e["kind"] == "override"]

    tasks_decomposed = len(all_tasks)
    halted_task_ids = {e["subject_id"] for e in disagreements_this_cycle}
    halt_events = len(disagreements_this_cycle)
    halt_rate = len(halted_task_ids) / tasks_decomposed if tasks_decomposed else 0.0
    override_rate = len(overrides_this_cycle) / halt_events if halt_events else 0.0

    cycle_times = []
    for t in ai_tasks:
        if t.status != "done" or not t.history:
            continue
        created_at = t.history[0]["at"]
        done_events = [h["at"] for h in t.history if h["action"] == "audit_pass"]
        if done_events:
            delta = (datetime.fromisoformat(done_events[-1]) - datetime.fromisoformat(created_at)).total_seconds()
            cycle_times.append(delta)
    avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0.0

    now = datetime.now(timezone.utc)
    board = store.load_task_board()
    stalled = [
        v for v in board.values()
        if v.get("owner") == "human" and v.get("status") != "done" and v.get("due")
        and datetime.fromisoformat(v["due"]) < now
    ]

    print(f"Tasks decomposed this cycle: {tasks_decomposed}")
    print(f"Halt rate: {len(halted_task_ids)}/{tasks_decomposed} distinct tasks halted = {halt_rate:.2%}")
    print(f"Override rate: {len(overrides_this_cycle)}/{halt_events} halt events resolved by override = {override_rate:.2%}")
    print(f"Avg AI-task cycle time (decompose -> audit pass): {avg_cycle_time:.2f}s over {len(cycle_times)} task(s)")
    print(f"Stalled human tasks (overdue, not done): {len(stalled)}")

    # ------------------------------------------------------------------ A
    print("\n-- ANALYZE --")
    root_causes: dict[str, list[dict]] = {}
    for e in disagreements_this_cycle:
        pattern = e.get("pattern") or "unspecified"
        root_causes.setdefault(pattern, []).append(e)
        print(f"  [{e['subject_id']}] pattern={pattern} source={e['source']}: {e['message'][:160]}...")

    if not disagreements_this_cycle:
        print("  No disagreements this cycle.")

    # ------------------------------------------------------------------ I
    print("\n-- IMPROVE --")
    newly_improved = []
    for pattern, entries in root_causes.items():
        if pattern in existing_patterns:
            print(f"  Pattern '{pattern}' already has a standing rule from a prior cycle -- not re-adding, "
                  f"Control (below) will check whether it actually held.")
            continue

        task_descs = sorted({task_by_id[e["subject_id"]].description for e in entries if e["subject_id"] in task_by_id})
        rule_text, marker_words = _craft_rule(pattern, task_descs, goals_by_id, task_by_id, entries)
        store.add_rule(rule_text, source=f"Learn cycle @ {run_started_at}", pattern=pattern, marker_words=marker_words)
        newly_improved.append(pattern)
        print(f"  NEW RULE for '{pattern}': {rule_text}")

    if not newly_improved and not root_causes:
        print("  Nothing to improve -- no new root causes this cycle.")

    # ------------------------------------------------------------------ C
    print("\n-- CONTROL --")
    control_results = []
    if not existing_patterns:
        print("  No rules existed before this cycle -- nothing to verify yet.")
    for pattern, rule in existing_patterns.items():
        recurred = len(root_causes.get(pattern, []))
        if recurred:
            msg = (f"Rule from {rule['added_at']} ('{rule['rule'][:90]}...') did NOT prevent recurrence -- "
                   f"{recurred} new instance(s) of '{pattern}' this cycle. Leaving OPEN.")
            store.log("control", "learn", pattern, msg, pattern=pattern)
            control_results.append({"pattern": pattern, "status": "open", "recurrences": recurred})
            print(f"  STILL OPEN: {msg}")
        else:
            msg = f"Rule from {rule['added_at']} held -- 0 recurrences of '{pattern}' this cycle. Marking RESOLVED."
            store.log("control", "learn", pattern, msg, pattern=pattern)
            control_results.append({"pattern": pattern, "status": "resolved", "recurrences": 0})
            print(f"  RESOLVED: {msg}")

    # ------------------------------------------------------------------ reminders
    print("\n-- FOUNDER REMINDERS --")
    reminders = []
    for v in stalled:
        msg = f"Reminder: human task [{v['id']}] '{v['description']}' was due {v['due']} and is still '{v['status']}'."
        reminders.append(msg)
        print(f"  {msg}")
    if not stalled:
        print("  None.")

    return {
        "halt_rate": halt_rate,
        "override_rate": override_rate,
        "avg_cycle_time": avg_cycle_time,
        "stalled_count": len(stalled),
        "newly_improved": newly_improved,
        "control_results": control_results,
        "reminders": reminders,
    }


def _craft_rule(pattern: str, task_descs: list[str], goals_by_id: dict, task_by_id: dict, entries: list[dict]) -> tuple[str, list[str]]:
    examples = "; ".join(task_descs[:3])

    if pattern.startswith("goal_drift:"):
        return (
            f"Root cause: task(s) [{examples}] are on-topic for their goal but the goal's metric names a "
            f"closing/final outcome that no task yet targets. Rule: when decomposing a goal whose metric "
            f"describes a commitment/signature/final state, always include at least one closing task that "
            f"explicitly targets it -- until then, Checker B's halts on this goal are expected, not a defect.",
            [],
        )

    if pattern.startswith("scope_creep:"):
        return (
            f"Root cause: task(s) [{examples}] share no vocabulary with their assigned goal. Rule: before "
            f"adding a task under a goal, confirm its description shares a concrete noun/verb with the goal "
            f"text, or route it under a more specific/new goal instead of the nearest existing one.",
            [],
        )

    if pattern == "unclassified_external_action":
        markers = sorted({m for e in entries for m in e.get("markers", [])})
        return (
            f"Root cause: task(s) [{examples}] are real external actions that THE CLASSIFIER's marker list "
            f"missed, caught only at routing-check by Checker C/D. Rule: widen THE CLASSIFIER's own "
            f"external-action markers with {markers or ['(see routing-check log)']} so these are caught at "
            f"first-pass classification, not just at routing-check.",
            markers,
        )

    if pattern == "unrecognized_judgment_call":
        return (
            f"Root cause: task(s) [{examples}] combine a judgment verb (identify/choose/select/worth/evaluate) "
            f"with a relational noun (mentor/investor/partner/supplier/client) -- a selection judgment, not "
            f"mechanical drafting -- that THE CLASSIFIER and Checker D both treat as safely ai_doable. Rule: "
            f"route the SELECTION step of such tasks to human_required; supporting research/drafting can stay "
            f"AI-doable as a separate task.",
            [],
        )

    return (f"Root cause: unclustered disagreement(s) on [{examples}]. Needs manual review.", [])
