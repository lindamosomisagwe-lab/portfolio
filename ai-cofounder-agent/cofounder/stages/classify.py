"""Stage 7: Classify -- for each surviving task, human-required or
AI-doable, with a reason. Real external action/communication is always
human-required, even if AI drafted the underlying content."""
from __future__ import annotations

from ..models import Task
from ..personas import classifier_classify


def run(tasks: list[Task]) -> list[Task]:
    print("\n=== CLASSIFY (THE CLASSIFIER) ===")
    for t in tasks:
        classification, reason = classifier_classify(t.description)
        t.classification = classification
        t.classification_reason = reason
        t.log("THE CLASSIFIER", "classified", f"{classification}: {reason}")
        print(f"  [{t.id}] {t.description}\n      -> {classification.upper()}: {reason}")
    return tasks
