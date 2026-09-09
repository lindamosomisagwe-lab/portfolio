# AI Cofounder Agent -- CLI Prototype

A runnable prototype of the pipeline described in the project brief: a
founder brings an idea they've already decided to act on, and the agent
turns it into a plan and goals, decomposes those into tasks, checks and
classifies each task, routes it to a human queue or an AI executor,
audits AI output, and runs a Learn/check-in cycle.

Idea validation/analysis (SWOT-style scoring of the business idea itself)
is out of scope for this prototype -- it starts at planning.

This is a CLI, not a UI, and there are no real bank/registration/social
integrations -- every "AI-doable" task produces a draft artifact for a
human to review, nothing is ever sent anywhere.

## Why the "AI" stages are simulated

No `ANTHROPIC_API_KEY` (or equivalent) is available in this environment,
and wiring one in would mean spending the founder's own API budget on a
demo. So every persona below is a deterministic, keyword/heuristic module
instead of a real model call -- but each one is architecturally isolated
behind a plain function, so swapping any single persona for a real LLM
call later is a one-function change, not a rewrite. Nothing in
`pipeline.py` or the stage modules needs to know or care whether a
persona is simulated or real.

## Personas (kept genuinely distinct, per the spec)

| Persona | Role | Stage |
|---|---|---|
| **THE SKEPTIC** | Align-checker -- distrusts decomposition by default, requires shared vocabulary with the stated goal | align_check |
| **THE CLASSIFIER** | Human-required vs AI-doable, with a reason. Deliberately narrower external-action rule set than THE INSPECTOR (see below) | classify |
| **THE INSPECTOR** | Routing-checker -- a rules-lawyer with a broader, harder external-action rule set. Differently prompted from THE SKEPTIC: not concerned with goal alignment at all | routing_check |
| **THE DOER** | The single shared executor for every AI-doable task. Branches only on generic task *shape* (research / draft-message / checklist), never on a specific task's identity | execute |
| **THE AUDITOR** | Checks output against the ask; rejects thin output and rejects any output that *claims* a real-world action was completed | audit |

The gap between THE CLASSIFIER's and THE INSPECTOR's external-action
rules is intentional -- it's what makes the routing-check checkpoint do
real work in the sample run (see below) instead of being a rubber stamp.

## Layout

```
cli.py                        entry point
cofounder/
  models.py                   Task, Goal, CheckResult, etc. (dataclasses)
  storage.py                  JSON persistence for the 4 stores in data/
  personas.py                 all persona logic (the "AI", simulated)
  io.py                       founder I/O: real input(), or a scripted queue
  pipeline.py                 orchestrates the pipeline stages
  stages/                     one module per pipeline stage
data/
  goal-context.json           founder's current plan + goals
  task-board.json             every task: status, owner, classification, history
  checker-rules.json          lessons accumulated by Learn
  audit-log.json              every halt, disagreement, override -- timestamped
sample_input.md               the raw idea used in the walkthrough below
sample_run_answers.json       scripted founder answers for a reproducible demo run
```

## Running it

Interactive, your own idea:
```
python3 cli.py run
```

Interactive, idea from a file:
```
python3 cli.py run --idea-file sample_input.md
```

Non-interactive demo run (scripted founder answers, reproduces the
walkthrough below exactly):
```
python3 cli.py run --idea-file sample_input.md --script sample_run_answers.json
```

`data/*.json` is written/updated as the run progresses. Delete the `data/`
files to start from a clean board.

## What the sample run demonstrates

Idea: a subscription box that rescues surplus/"ugly" produce from local
farms and delivers it to households at a discount.

1. **Idea intake** -- idea is submitted, pipeline proceeds straight to
   planning (no idea-validation stage in this prototype).
2. **Plan and goals** -- founder states resources/time/constraints; four
   goals are drafted from them (validate demand, line up suppliers,
   secure funding, stand up legal/banking basics).
3. **Decompose** -- 13 tasks generated, including the seed AI-doable
   examples from the spec (find funding sources, identify mentors,
   draft outreach, draft application docs, prep a bank-account checklist)
   and one task -- "Design company swag..." -- deliberately left
   disconnected from any goal.
4. **Align check (andon cord)** -- THE SKEPTIC halts exactly that one
   task (0.00 vocabulary overlap with its nominal goal) and logs it
   instead of dropping it silently. The founder is asked and drops it.
5. **Classify** -- THE CLASSIFIER marks "Post a signup announcement in
   local Facebook community groups..." as **ai_doable** (its rule set
   doesn't cover "post").
6. **Routing check** -- THE INSPECTOR disagrees: posting to a public
   channel is a real external action, always human-required. HALT,
   logged as a disagreement, not auto-resolved. Founder accepts the
   correction.
7. **Route** -- 4 tasks to the human queue (call a supplier, submit the
   funding application, file the business registration, and the
   corrected Facebook-post task), 8 to the AI queue.
8. **Execute** -- all 8 AI-doable tasks run through THE DOER concurrently
   (`ThreadPoolExecutor`), independent tasks like funding-source research
   and mentor-outreach drafting genuinely running in parallel.
9. **Audit** -- THE AUDITOR checks every output against its task before
   marking it done; all 8 pass in this run (audit rejects thin output
   and any output claiming a completed real-world action).
10. **Learn / check-in** -- the routing-check override becomes a
    persisted rule ("add post/publish to THE CLASSIFIER's own markers"),
    and the overdue human task (simulated as already past due, to
    exercise this check) produces a founder reminder.

Full transcript is reproducible by running the scripted command above;
resulting state is in `data/*.json` after running it.
