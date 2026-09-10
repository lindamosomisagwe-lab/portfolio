"""Stage 5: Decompose -- break goals into concrete, assignable tasks.

Task lists are templated per goal category (a real system would follow a
similar playbook-per-goal-type approach). One task below is deliberately
left disconnected from any goal's actual substance -- decomposition drift
happens in real teams, and the align-check stage exists to catch exactly
this rather than let it slide through silently.
"""
from __future__ import annotations

from ..models import Goal, Task, new_id


def _find(goals: list[Goal], keyword: str) -> Goal:
    return next(g for g in goals if keyword in g.text.lower())


def run(goals: list[Goal]) -> list[Task]:
    demand = _find(goals, "demand")
    partners = _find(goals, "partner")
    funding = _find(goals, "funding")
    legal = _find(goals, "legal")

    tasks: list[Task] = []

    def add(goal: Goal, description: str) -> None:
        tasks.append(Task(id=new_id("task"), goal_id=goal.id, description=description))

    add(demand, "Draft landing page copy describing the offer to gauge signup demand")
    add(demand, "Post a signup announcement in local Facebook community groups to validate demand")
    add(demand, "Collect and tabulate signups from the demand-validation page")

    add(partners, "Identify local farms/suppliers that match our sourcing needs")
    add(partners, "Schedule a call with each shortlisted supplier to discuss terms")

    add(funding, "Find funding sources matching our stage and industry")
    add(funding, "Identify mentors or investors worth contacting")
    add(funding, "Draft an outreach message to a prospective mentor")
    add(funding, "Draft documentation for a funding application")
    add(funding, "Submit the completed funding application")

    add(legal, "Prepare a checklist for opening a business bank account")
    add(legal, "File the business registration with the state")

    # Deliberate goal-drift task for the align-checker to catch.
    add(funding, "Design company swag and merchandise for a future launch party")

    print("\n=== DECOMPOSITION ===")
    for t in tasks:
        print(f"  [{t.id}] (goal {t.goal_id}) {t.description}")

    return tasks
