# AI Cofounder Agent -- CLI Prototype

A runnable prototype of the pipeline described in the project brief: a
founder brings an idea they've already decided to act on, and the agent
turns it into a plan and goals, decomposes those into tasks, runs each
checkpoint through two independently-prompted checkers, routes tasks to
a human queue or an AI executor, audits AI output, and runs a real
DMAIC Learn/check-in cycle.

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

## Multi-agent checking: two checkers per checkpoint, never a vote

Each checkpoint used to be one doer + one checker. It's now one doer +
**two independently-prompted checkers**, and the three are never voted
or averaged. Any disagreement -- between the two checkers, or between
either checker and the doer -- halts the task and logs the *specific*
disagreement (each persona's own verdict and reasoning) for the founder
to resolve. Consensus is required, not majority.

| Persona | Role | Checks against |
|---|---|---|
| **CHECKER A** (scope creep) | Align-checker -- is the task even about the goal's *topic*? | `goal.text` |
| **CHECKER B** (goal drift) | Align-checker -- if so, does it actually move the goal's *stated metric*? | `goal.metric` |
| **CHECKER C** (over-automation) | Routing-checker -- flags hard external actions **and** relational/judgment calls (choosing *who* to pursue) marked ai_doable | task text |
| **CHECKER D** (under-automation) | Routing-checker -- flags only hard external actions; doesn't buy soft judgment arguments, biased toward ai_doable | task text |
| **THE CLASSIFIER** | First-pass human/AI classification (the doer at the routing checkpoint) -- deliberately narrower marker list than C/D | task text |
| **THE DOER** | Single shared executor for every AI-doable task | task text |
| **THE AUDITOR** | Checks output against the ask; rejects thin output and any output claiming a completed real-world action | task + output |

A and B compare against *different reference text* (topic vs. metric) so
they can genuinely disagree with each other, not just echo the doer. C
and D compare the same text but start from opposite priors (suspicious of
automation vs. suspicious of over-caution), so they too can land on
opposite recommendations for the same task -- see the real example below.

### A real checker-vs-checker disagreement (not checker-vs-doer)

Routing check on `"Identify local farms/suppliers that match our sourcing needs"`:

```
THE CLASSIFIER (doer): AI_DOABLE -- research/drafting, no real-world action.
CHECKER C (over-automation): HUMAN_REQUIRED -- asks someone to identify which
    suppliers to pursue -- that's a relational/business judgment call, not
    mechanical drafting. The research can stay AI-drafted, but the actual
    selection needs a human.
CHECKER D (under-automation): AI_DOABLE -- No real external action here.
    Selecting candidates from a shortlist is still just producing a
    reviewable draft -- I don't see grounds to route this to a human.
-> DISAGREEMENT, not unanimous. Logging as open, not auto-resolving.
```

THE CLASSIFIER and CHECKER D land on `ai_doable`; CHECKER C independently
lands on `human_required` -- for the same task, from the same input text.
That's a genuine split between two checkers, not one checker overriding a
doer that never had an opinion. The founder resolves it (in the sample
run: sides with C here, but overrides C the other way on a near-identical
mentor-selection task -- see the transcript).

## Real DMAIC, not a vague periodic review

Learn used to be "review the board, write a note." It's now five actual
phases, every cycle:

- **Define** -- name the numbers: halt rate, override rate, avg AI-task
  cycle time, count of stalled human tasks.
- **Measure** -- compute them from `task-board.json` + `audit-log.json`,
  scoped to timestamps `>= this run's start`.
- **Analyze** -- every halt/override this cycle is clustered by a
  `pattern` tag (e.g. `goal_drift:<goal-slug>`, `unrecognized_judgment_call`)
  attached at the moment the checker dissents -- not guessed after the fact.
- **Improve** -- one new rule per *newly seen* root cause, written to
  `checker-rules.json`. A pattern that already has a rule from a prior
  cycle is **not** re-written -- Control (below) checks whether the
  existing rule actually worked instead.
  Some rules are machine-actionable: an `unclassified_external_action`
  rule carries the actual matched marker regexes in a `marker_words`
  field, and `classify.py` reads them back out to widen THE CLASSIFIER's
  own marker list on the *next* run -- the system genuinely gets smarter
  between cycles, not just accumulates prose nobody acts on.
- **Control** -- for every rule that existed *before* this cycle, check
  whether its `pattern` recurred this cycle anyway. Recurred -> logged as
  **still open**, not resolved, regardless of the rule existing. Zero
  recurrence -> logged **resolved**.

Reminders for stalled human tasks are generated separately, from the
whole persisted queue (not just this cycle's tasks).

### One real cycle, with before/after numbers

Running the same idea and founder answers twice (`sample_run_answers.json`
then `sample_run_answers_cycle2.json`, back to back, without wiping
`data/`) produces:

| Metric | Cycle 1 | Cycle 2 |
|---|---|---|
| Halt rate | 5/13 tasks = 38.46% | 4/13 tasks = 30.77% |
| Override rate | 5/8 halt events = 62.50% | 4/6 halt events = 66.67% |
| Avg AI-task cycle time | 0.02s (7 tasks) | 0.03s (7 tasks) |
| Stalled human tasks (whole queue) | 1 | 2 (accumulates) |

Cycle 1's Improve step wrote 5 rules. Cycle 2's Control step checked all 5:

```
RESOLVED: Rule ... held -- 0 recurrences of 'unclassified_external_action'
    this cycle. Marking RESOLVED.
STILL OPEN: Rule ... did NOT prevent recurrence -- 2 new instance(s) of
    'goal_drift:line_up_the_external_partners_suppliers_' this cycle.
STILL OPEN: Rule ... did NOT prevent recurrence -- 1 new instance(s) of
    'scope_creep:secure_enough_funding_and_investor_mento' this cycle.
STILL OPEN: Rule ... did NOT prevent recurrence -- 1 new instance(s) of
    'goal_drift:secure_enough_funding_and_investor_mento' this cycle.
STILL OPEN: Rule ... did NOT prevent recurrence -- 2 new instance(s) of
    'unrecognized_judgment_call' this cycle.
```

The one resolved rule is the one that was actually wired into code (the
`marker_words` mechanism above) -- `classify.py` now classifies "Post a
signup announcement..." as `human_required` on the first pass, so the
routing-check disagreement that fired in cycle 1 simply doesn't recur:
the halt rate drop (38.46% -> 30.77%) is exactly that one task's disagreement
disappearing from both checkpoints' halt counts. The other four rules are
prose-only recommendations nobody has implemented yet (no code change to
`decompose.py`'s goal templates or to Checker C's judgment-call logic) --
Control correctly refuses to call them resolved just because a rule
exists, and keeps logging real recurrences every cycle until someone
actually fixes the root cause.

## Layout

```
cli.py                            entry point
cofounder/
  models.py                       Task, Goal, AuditLogEntry, etc. (dataclasses)
  storage.py                      JSON persistence for the 4 stores in data/
  personas.py                     all persona logic (the "AI", simulated)
  io.py                           founder I/O: real input(), or a scripted queue
  pipeline.py                     orchestrates the pipeline stages
  stages/                         one module per pipeline stage
data/
  goal-context.json                founder's current plan + goals
  task-board.json                  every task: status, owner, classification, history
  checker-rules.json               lessons accumulated by Learn (with pattern/marker_words)
  audit-log.json                   every halt, disagreement, override, control check -- timestamped
sample_input.md                    the raw idea used in the walkthrough
sample_run_answers.json            scripted founder answers -- cycle 1 (baseline)
sample_run_answers_cycle2.json     scripted founder answers -- cycle 2 (Control verification)
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

Non-interactive demo run, cycle 1 (baseline -- wipe `data/` first for a clean board):
```
rm -f data/*.json
python3 cli.py run --idea-file sample_input.md --script sample_run_answers.json
```

Non-interactive demo run, cycle 2 (Control verification -- run right after
cycle 1, without wiping `data/`, so checker-rules.json carries over):
```
python3 cli.py run --idea-file sample_input.md --script sample_run_answers_cycle2.json
```

## What the sample run demonstrates

Idea: a subscription box that rescues surplus/"ugly" produce from local
farms and delivers it to households at a discount.

1. **Idea intake** -- idea is submitted, pipeline proceeds straight to
   planning (no idea-validation stage in this prototype).
2. **Plan and goals** -- founder states resources/time/constraints; four
   goals are drafted from them (validate demand, line up suppliers,
   secure funding + investor/mentor support, stand up legal/banking basics).
3. **Decompose** -- 13 tasks generated, including the seed AI-doable
   examples from the spec, and one task -- "Design company swag..." --
   deliberately left disconnected from any goal.
4. **Align check** -- CHECKER A and CHECKER B independently review every
   task. The swag task fails both (unanimous halt, still logged as a
   disagreement against the doer). Two more tasks (`Identify local
   farms/suppliers...`, `Schedule a call with each shortlisted supplier...`)
   pass A (clearly about supplier partnerships) but fail B (goal2's metric
   demands a *signed* partnership, and neither task is a closing action) --
   a genuine A-vs-B split. Founder keeps both, drops the swag task.
5. **Classify** -- THE CLASSIFIER's narrower marker list misses "post" as
   an external action.
6. **Routing check** -- CHECKER C and D review every task independently.
   The Facebook-post task: both flag it as `human_required` (hard
   external-action floor), disagreeing with the doer. The
   supplier/mentor-identification tasks: CHECKER C flags them as
   relational/judgment calls while CHECKER D and the doer both say
   `ai_doable` -- the real checker-vs-checker split shown above. Founder
   resolves each independently (not identically).
7. **Route / Execute / Audit** -- unchanged in spirit: human-required
   tasks queue for a human, AI-doable tasks run in parallel through the
   one shared executor, and every output is audited before being marked
   done.
8. **Learn (DMAIC)** -- see the before/after table above.

Full transcripts are reproducible by running the two scripted commands
above in order; resulting state is in `data/*.json` after running both.
