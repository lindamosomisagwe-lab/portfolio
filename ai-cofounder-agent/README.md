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

## Two ways to run this -- no external API call, either way

There's no `ANTHROPIC_API_KEY` in play here, and there never has been --
using one would mean spending the founder's own money on a demo. But an
LLM doesn't need a separate API call to reason as these personas when
one is already running the session:

- **Live, in-session reasoning (canonical -- what `data/*.json` reflects
  right now).** Claude Code itself reads the idea and genuinely reasons
  through every checker's judgment, the executor's drafts, and the DMAIC
  analysis -- then writes the results straight to the JSON stores. No
  code path "plays" the personas; a person (well, an LLM) actually does.
  This is what produced the current `data/` contents and the walkthrough
  below.
- **Deterministic script (`cli.py` + `cofounder/`).** The same pipeline
  shape, but every persona is a keyword/regex heuristic instead of real
  judgment, so it can run unattended, offline, without any LLM present
  at all (`python3 cli.py run --script sample_run_answers.json`). Good
  for a fully automatable demo or as a architecture reference; its
  reasoning is necessarily cruder than the live version -- see the
  contrast below.

Both share the same persona roster, the same JSON schema, and the same
"never vote, log the disagreement" rule. Only *who's doing the thinking*
differs.

### Where live reasoning actually did better

Running this live surfaced a real gap in the keyword-heuristic version.
The regex Checker B (goal drift) used blunt vocabulary overlap and
couldn't tell "Identify local farms/suppliers..." (pure candidate
curation) from "Schedule a call with each shortlisted supplier to
discuss terms" (where a verbal commitment could actually happen in that
same task) -- it flagged both, or neither, depending on shared keywords,
not on which task's own scope could plausibly produce the goal's metric.
Reasoning through it live, Checker B draws that distinction on purpose:
it halts the curation task and passes the negotiation task, because only
the negotiation task's own deliverable can be the commitment the metric
asks for. That's the kind of judgment call keyword overlap can't make.

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
opposite recommendations for the same task.

### A real checker-vs-checker disagreement (not checker-vs-doer)

Routing check on `"Identify local farms/suppliers that match our sourcing needs"`:

```
THE CLASSIFIER (doer): AI_DOABLE -- reads as research/listing.
CHECKER C (over-automation): HUMAN_REQUIRED -- choosing WHICH specific
    businesses to approach for a partnership is a real business judgment
    call about which relationships to invest time in -- not mechanical
    drafting. The research can stay AI-drafted, but the actual selection
    should have a human's sign-off.
CHECKER D (under-automation): AI_DOABLE -- this is still just producing
    a shortlist -- no actual contact happens in this task. I don't see
    grounds to route mere candidate-narrowing to a human.
-> DISAGREEMENT, not unanimous. Logging as open, not auto-resolving.
```

THE CLASSIFIER and CHECKER D land on `ai_doable`; CHECKER C independently
lands on `human_required` -- for the same task, from the same input text.
The founder sided with D here (kept it AI-doable). The *exact same*
disagreement recurred one task later, on `"Identify mentors or investors
worth contacting"` -- and this time the founder sided with C (made it
human_required), reasoning that mentor/investor relationships are
higher-stakes than supplier sourcing. Both calls are defensible on their
own, but they're inconsistent with each other, and Learn's Analyze step
below calls that out explicitly rather than pretending the founder had
one coherent policy.

## Real DMAIC, not a vague periodic review

Learn is five actual phases, every cycle:

- **Define** -- name the numbers: halt rate, override rate, avg AI-task
  cycle time, count of stalled human tasks.
- **Measure** -- compute them from `task-board.json` + `audit-log.json`,
  scoped to this cycle.
- **Analyze** -- every halt/override this cycle, clustered by a `pattern`
  tag (e.g. `goal_drift:goal-partners`, `unrecognized_judgment_call`)
  attached at the moment the checker dissents -- not guessed after the
  fact. Includes calling out real inconsistencies, like the founder's
  opposite resolutions on the supplier/mentor pair above.
- **Improve** -- one concrete rule per root cause, written to
  `checker-rules.json`. Some rules are machine-actionable: the
  `unclassified_external_action` rule carries the actual marker regexes
  (`\bpost\b`, `\bpublish\b`) in a `marker_words` field, which the
  deterministic script's `classify.py` reads back out to widen its own
  marker list on the next run -- a genuine self-improvement loop, not
  just prose nobody acts on. (In the live-reasoning mode, "acting on the
  rule" means it now sits in the record for the next live cycle's
  Control step to check against.)
- **Control** -- for every rule that existed *before* this cycle, check
  whether its pattern recurred anyway. Recurred -> **still open**, not
  resolved, regardless of the rule existing. This cycle is the first one
  for the live-reasoning run, so there's nothing to verify yet -- Control
  says exactly that rather than fabricating a result. (The deterministic
  script's `sample_run_answers.json` + `sample_run_answers_cycle2.json`
  pair demonstrates what a second cycle's Control step looks like: 1
  rule resolved, 4 still open, with real before/after halt-rate numbers
  -- run both back to back to reproduce it.)

### This cycle's real numbers (live-reasoning run)

| Metric | Value |
|---|---|
| Tasks decomposed | 13 |
| Halt rate | 4/13 distinct tasks = 30.77% |
| Override rate | 5/8 halt events = 62.50% |
| Avg AI-task cycle time | 685.7s (~11.4 min) over 7 tasks |
| Stalled human tasks | 1 |

Five rules were written this cycle, one per root cause: two `goal_drift`
rules (goal-partners, goal-funding), one `scope_creep` rule, the
machine-actionable `unclassified_external_action` rule, and the
`unrecognized_judgment_call` rule that also flags the founder's own
inconsistent resolution as something worth revisiting on purpose.

## Layout

```
cli.py                            entry point (deterministic-script mode)
cofounder/
  models.py                       Task, Goal, AuditLogEntry, etc. (dataclasses)
  storage.py                      JSON persistence for the 4 stores in data/
  personas.py                     all persona logic (keyword/regex heuristics, deterministic-script mode only)
  io.py                           founder I/O: real input(), or a scripted queue
  pipeline.py                     orchestrates the pipeline stages
  stages/                         one module per pipeline stage
data/
  goal-context.json                founder's current plan + goals
  task-board.json                  every task: status, owner, classification, history
  checker-rules.json               lessons accumulated by Learn (with pattern/marker_words)
  audit-log.json                   every halt, disagreement, override, control check -- timestamped
sample_input.md                    the raw idea used in the walkthrough
sample_run_answers.json            scripted founder answers -- deterministic-script cycle 1 (baseline)
sample_run_answers_cycle2.json     scripted founder answers -- deterministic-script cycle 2 (Control verification)
```

`data/*.json` right now holds the **live-reasoning** run's output (see
above). Running the deterministic script will overwrite it with its own
(cruder) version of the same idea -- see below if you want that instead.

## Running it

**Live reasoning** (what's in `data/` now): there's no command for this
-- it's Claude Code reasoning through the idea directly in a session and
writing the JSON files, the way this README's numbers were produced.
Ask an active Claude Code session to run the agent on a new idea to
reproduce it.

**Deterministic script**, interactive, your own idea:
```
python3 cli.py run
```

Deterministic script, idea from a file:
```
python3 cli.py run --idea-file sample_input.md
```

Deterministic script, non-interactive demo, cycle 1 (baseline -- wipe
`data/` first for a clean board; this will replace the live-reasoning
output above with the keyword-heuristic version):
```
rm -f data/*.json
python3 cli.py run --idea-file sample_input.md --script sample_run_answers.json
```

Deterministic script, cycle 2 (Control verification -- run right after
cycle 1, without wiping `data/`):
```
python3 cli.py run --idea-file sample_input.md --script sample_run_answers_cycle2.json
```

## What the live-reasoning sample run demonstrates

Idea: a subscription box that rescues surplus/"ugly" produce from local
farms and delivers it to households at a discount.

1. **Idea intake** -- idea is submitted, pipeline proceeds straight to
   planning (no idea-validation stage in this prototype).
2. **Plan and goals** -- founder states resources/time/constraints; four
   goals are drafted from them (validate demand, line up suppliers,
   secure funding + investor/mentor support, stand up legal/banking basics).
3. **Decompose** -- 13 tasks, including one -- "Design company swag..."
   -- deliberately left disconnected from any goal.
4. **Align check** -- CHECKER A and B independently review every task.
   `"Identify local farms/suppliers..."` and `"Identify mentors or
   investors worth contacting"` both pass A (clearly on-topic) but fail
   B (curating a candidate list doesn't itself create the signed/verbal
   commitment their goals' metrics require) -- two genuine A-vs-B splits
   sharing one root cause. The swag task fails both (unrelated to any
   goal). Founder keeps the two curation tasks, drops the swag task.
5. **Classify** -- THE CLASSIFIER's narrower marker list misses "post"
   as an external action.
6. **Routing check** -- CHECKER C and D independently review every task.
   The Facebook-post task: both flag it `human_required` (publishing
   publicly is a real action), disagreeing with the doer. The
   supplier/mentor-identification tasks: CHECKER C flags them as
   relational/judgment calls while CHECKER D and the doer both say
   `ai_doable` -- the real checker-vs-checker split above, resolved
   inconsistently by the founder across the two near-identical tasks.
7. **Route / Execute / Audit** -- 7 tasks go AI-doable, 5 human-required,
   1 dropped. THE DOER drafts real, substantive content for each
   AI-doable task (a landing page, a supplier shortlist, a funding-source
   shortlist, an outreach message, funding-application docs, a
   bank-account checklist) -- not placeholder text. THE AUDITOR actually
   rejects the first draft of the funding-application docs (too many
   unfilled `[placeholder]` fields for a usable starting point) and
   passes the revision.
8. **Learn (DMAIC)** -- see the numbers above; Analyze explicitly flags
   the founder's inconsistent resolution of the two identical-shape
   disagreements as something to resolve on purpose next time.

Full task-by-task reasoning, every draft, and the complete audit trail
are in `data/*.json`.
