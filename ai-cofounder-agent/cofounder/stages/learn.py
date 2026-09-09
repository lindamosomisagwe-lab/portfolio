"""Stage 11: Learn and check in -- review the board for checker mistakes
caught by human override, persist lessons to checker-rules, and remind
the founder about overdue/stalled human-owned tasks."""
from __future__ import annotations

from datetime import datetime, timezone

from ..models import Task
from ..storage import Store


def run(store: Store, align_halted: list[Task], routing_disagreements: list[Task], human_tasks: list[Task]) -> dict:
    print("\n=== LEARN / CHECK-IN ===")
    rules_added: list[str] = []

    for t in align_halted:
        if t.status == "aligned":
            # Founder overrode -- the align-checker was too strict on this one.
            rule = (
                f"Align-check flagged '{t.description}' as unrelated to its goal, but the founder "
                f"kept it. Treat low-overlap flags on tasks tied to launch/marketing prep as "
                f"lower-confidence -- ask before assuming drift."
            )
            store.add_rule(rule, "THE SKEPTIC (align-checker) override")
            rules_added.append(rule)
        elif t.status == "dropped":
            rule = (
                f"Align-check correctly caught goal-drift on '{t.description}' (founder dropped it). "
                f"No change needed -- reinforces the current overlap threshold."
            )
            # Informational, not a behavior change -- log but don't clutter the rules file.
            store.log("info", "learn", t.id, rule)

    for t in routing_disagreements:
        if "Corrected by founder" in (t.classification_reason or ""):
            rule = (
                f"THE CLASSIFIER marked '{t.description}' ai_doable but it involved a public-channel "
                f"post; THE INSPECTOR caught it and the founder confirmed the correction. "
                f"Add 'post'/'publish' to the classifier's own external-action markers so this is "
                f"caught on the first pass next time, not just at routing-check."
            )
            store.add_rule(rule, "THE INSPECTOR (routing-checker) override")
            rules_added.append(rule)

    now = datetime.now(timezone.utc)
    reminders = []
    for t in human_tasks:
        if t.status != "done" and t.due:
            due_dt = datetime.fromisoformat(t.due)
            if due_dt < now:
                msg = f"Reminder: human task [{t.id}] '{t.description}' was due {t.due} and is still '{t.status}'."
                reminders.append(msg)
                store.log("info", "learn", t.id, msg)

    print(f"New checker rules learned this cycle: {len(rules_added)}")
    for r in rules_added:
        print(f"  - {r}")
    print(f"Founder reminders: {len(reminders)}")
    for r in reminders:
        print(f"  - {r}")

    return {"rules_added": rules_added, "reminders": reminders}
