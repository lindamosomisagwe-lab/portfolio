"""Stage 2: Validate -- SWOT analysis on the raw idea, presented to the founder."""
from __future__ import annotations

from ..personas import analyst_swot


def run(idea_text: str) -> dict:
    report = analyst_swot(idea_text)
    print("\n=== VALIDATION (THE ANALYST -- SWOT) ===")
    for section in ("strengths", "weaknesses", "opportunities", "threats"):
        print(f"\n{section.upper()}:")
        for line in report[section]:
            print(f"  - {line}")
    return report
