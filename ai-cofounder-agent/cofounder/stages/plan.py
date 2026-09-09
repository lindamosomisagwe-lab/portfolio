"""Stage 4: Plan and goals -- ask the founder what they actually have, draft
a lightweight plan and a concrete goal set from it."""
from __future__ import annotations

from ..io import FounderIO
from ..models import Goal, new_id


def run(io: FounderIO, idea_text: str) -> tuple[dict, list[Goal]]:
    resources = io.ask("What resources do you have (people, money, existing assets)?")
    time_budget = io.ask("How much time per week can the team actually commit?")
    constraints = io.ask("What constraints or deadlines matter most right now?")

    plan_context = {
        "idea": idea_text,
        "resources": resources,
        "time_budget": time_budget,
        "constraints": constraints,
    }

    print("\n=== PLAN (drafted from your constraints) ===")
    print(f"Resources on hand: {resources}")
    print(f"Time budget: {time_budget}")
    print(f"Binding constraints: {constraints}")

    # Generic early-stage goal template, parameterized by what the founder
    # actually said -- not hardcoded to a specific idea.
    goals = [
        Goal(
            id=new_id("goal"),
            text="Validate real demand before committing further resources",
            metric=f"Concrete evidence of demand (signups, pre-orders, or paid pilots), "
                    f"gathered within: {constraints}",
        ),
        Goal(
            id=new_id("goal"),
            text="Line up the external partners/suppliers the idea depends on",
            metric="Signed or verbally-committed partnerships with named counterparties",
        ),
        Goal(
            id=new_id("goal"),
            text="Secure enough funding and investor/mentor support to operate within the stated time budget",
            metric=f"Funding or committed budget sufficient given: {resources}",
        ),
        Goal(
            id=new_id("goal"),
            text="Stand up the minimum legal/operational scaffolding to trade legally",
            metric="Business registration and banking prerequisites identified and queued",
        ),
    ]

    print("\nGOALS:")
    for g in goals:
        print(f"  [{g.id}] {g.text}  (metric: {g.metric})")

    return plan_context, goals
