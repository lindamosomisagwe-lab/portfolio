"""Stage: Routing check -- two independently-prompted checkers review the
classification:

  CHECKER C (over-automation)  -- flags hard external actions AND
                                   relational/judgment calls marked ai_doable
  CHECKER D (under-automation) -- flags nothing but hard external actions;
                                   otherwise biased toward ai_doable

They are never voted or averaged, against each other or against the doer
(THE CLASSIFIER's first-pass call). Any disagreement among the three --
C vs D, C vs classifier, D vs classifier -- HALTS the task and logs the
specific disagreement. The founder picks the final classification;
nothing is auto-resolved.
"""
from __future__ import annotations

from ..io import FounderIO
from ..models import Task
from ..personas import checker_c_over_automation, checker_d_under_automation
from ..storage import Store


def run(io: FounderIO, tasks: list[Task], store: Store) -> tuple[list[Task], list[Task]]:
    print("\n=== ROUTING CHECK (CHECKER C -- over-automation, CHECKER D -- under-automation) ===")
    disagreements: list[Task] = []

    for t in tasks:
        c = checker_c_over_automation(t.description)
        d = checker_d_under_automation(t.description)

        voices = [
            ("THE CLASSIFIER (doer)", t.classification, t.classification_reason),
            (c.persona, c.classification, c.reasoning),
            (d.persona, d.classification, d.reasoning),
        ]
        distinct = {v[1] for v in voices}

        print(f"  [{t.id}] {t.description}")
        for name, classification, reasoning in voices:
            print(f"      {name}: {classification.upper()} -- {reasoning}")

        if len(distinct) == 1:
            t.log("routing_check", "unanimous_pass", "Classifier, Checker C, and Checker D all agree.")
            continue

        disagreement_lines = [f"{name}: {classification.upper()} -- {reasoning}" for name, classification, reasoning in voices]
        summary = " | ".join(disagreement_lines)
        print("      -> DISAGREEMENT, not unanimous. Logging as open, not auto-resolving.")

        t.status = "halted"
        t.log("routing_check", "disagreement", summary)
        for verdict in (c, d):
            if verdict.classification != t.classification:
                store.log("disagreement", verdict.persona, t.id, summary,
                           pattern=verdict.pattern, markers=verdict.matched_markers)
        disagreements.append(t)

    if disagreements:
        print(f"\n{len(disagreements)} classification disagreement(s). Founder must resolve each.")
        for t in disagreements:
            answer = io.ask(
                f"Task [{t.id}] '{t.description}': checkers disagree (see above). "
                f"Final classification -- human_required (h) or ai_doable (a)?"
            )
            old = t.classification
            final = "human_required" if answer.strip().lower().startswith("h") else "ai_doable"
            t.classification = final
            t.classification_reason = f"Resolved by founder after routing-check disagreement: {final}."
            t.status = "aligned"
            t.log("founder", "resolve_routing_disagreement", f"{old} -> {final}")
            store.log("override", "founder", t.id, f"Founder resolved routing-check disagreement: {old} -> {final}")

    return tasks, disagreements
