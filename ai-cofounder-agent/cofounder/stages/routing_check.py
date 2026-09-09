"""Stage 8: Routing check -- THE INSPECTOR, a second and differently-
prompted checker, reviews the classification. On disagreement: HALT that
task and log it rather than resolving automatically."""
from __future__ import annotations

from ..io import FounderIO
from ..models import Task
from ..personas import inspector_check_classification
from ..storage import Store


def run(io: FounderIO, tasks: list[Task], store: Store) -> tuple[list[Task], list[Task]]:
    print("\n=== ROUTING CHECK (THE INSPECTOR) ===")
    disagreements: list[Task] = []

    for t in tasks:
        verdict = inspector_check_classification(t.description, t.classification)
        print(f"  [{t.id}] {t.description} (classified: {t.classification})")
        print(f"      -> {verdict.verdict.upper()}: {verdict.reasoning}")

        if verdict.verdict == "halt":
            t.status = "halted"
            t.log("THE INSPECTOR", "routing_check_disagreement", verdict.reasoning)
            store.log("disagreement", "THE INSPECTOR (routing-checker)", t.id, verdict.reasoning)
            disagreements.append(t)
        else:
            t.log("THE INSPECTOR", "routing_check_pass", verdict.reasoning)

    if disagreements:
        print(f"\n{len(disagreements)} classification disagreement(s). Founder must resolve each.")
        for t in disagreements:
            answer = io.ask(
                f"Task [{t.id}] '{t.description}': classifier said '{t.classification}', "
                f"INSPECTOR disagrees and says human_required. Accept the INSPECTOR's correction? (y/n)"
            )
            old = t.classification
            if answer.strip().lower().startswith("y"):
                t.classification = "human_required"
                t.classification_reason = "Corrected by founder after routing-check disagreement: " + \
                    "involves a real external action, must be human-required."
                t.status = "aligned"
                t.log("founder", "override_classification", f"{old} -> human_required")
                store.log("override", "founder", t.id, f"Founder accepted INSPECTOR correction: {old} -> human_required")
            else:
                t.status = "aligned"
                t.log("founder", "keep_classification", f"Founder kept classification '{old}' despite disagreement.")
                store.log("override", "founder", t.id, f"Founder overrode INSPECTOR and kept classification '{old}'.")

    return tasks, disagreements
