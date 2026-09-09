"""Stage: Classify -- for each surviving task, human-required or
AI-doable, with a reason. Real external action/communication is always
human-required, even if AI drafted the underlying content.

Reads persisted checker-rules for any `marker_words` a previous Learn
cycle's Improve step attached -- this is how the system actually gets
smarter between runs, not just writes notes nobody acts on."""
from __future__ import annotations

from ..models import Task
from ..personas import classifier_classify
from ..storage import Store


def run(tasks: list[Task], store: Store) -> list[Task]:
    rules = store.load_rules()
    extra_markers = sorted({m for r in rules for m in r.get("marker_words", [])})
    if extra_markers:
        print(f"\n(THE CLASSIFIER has learned {len(extra_markers)} extra marker(s) from prior cycles: {extra_markers})")

    print("\n=== CLASSIFY (THE CLASSIFIER) ===")
    for t in tasks:
        classification, reason = classifier_classify(t.description, extra_markers=extra_markers)
        t.classification = classification
        t.classification_reason = reason
        t.log("THE CLASSIFIER", "classified", f"{classification}: {reason}")
        print(f"  [{t.id}] {t.description}\n      -> {classification.upper()}: {reason}")
    return tasks
