"""
Distinct personas used throughout the pipeline.

No real LLM is wired in (no API key available in this environment, and
calling one would cost real money the user didn't ask to spend). Each
persona is a deterministic, template/heuristic module -- but each has a
genuinely different focus, tone, and pass/fail criteria, so the
architecture demonstrates real separation of concerns. Swapping any one
of these for a real model call later means implementing the same
function signature; nothing upstream or downstream changes.

Personas:
  - CHECKER A (scope creep)    : align-checker -- flags tasks unrelated
                                  to the goal's TOPIC
  - CHECKER B (goal drift)     : align-checker -- flags tasks that are
                                  on-topic but don't clearly advance the
                                  goal's stated success METRIC
  - CHECKER C (over-automation): routing-checker -- flags relational/
                                  judgment tasks and hard external actions
  - CHECKER D (under-automation): routing-checker -- flags nothing except
                                  hard external actions; defaults to
                                  ai_doable otherwise, biased against
                                  over-classifying as human
  - THE CLASSIFIER              : first-pass human/AI classification (doer
                                  for the routing checkpoint)
  - THE DOER                    : single shared executor for all AI-doable
                                  tasks
  - THE AUDITOR                 : checks output against the ask

Checkers A vs B and C vs D are independently prompted -- each computes its
own verdict from scratch. They are never voted or averaged against each
other or against the doer: any disagreement between them, or between
either of them and the doer, halts and gets logged as open for the
founder to resolve.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "with",
    "our", "we", "will", "is", "are", "be", "at", "by", "from", "that",
    "this", "as", "it", "its", "into", "about", "up", "out", "within",
}

# Verbs/phrases that mean "this touches the real world" -- per the spec,
# any task carrying one of these is ALWAYS human-required, even if an AI
# drafted the underlying content. Both routing checkers (C and D) treat
# this list as a non-negotiable floor.
EXTERNAL_ACTION_MARKERS = [
    r"\bsend\b", r"\bsent\b", r"\bemail\b(?!.*draft)", r"\bcall\b", r"\bcontact\b",
    r"\bpost\b", r"\bpublish\b", r"\bfile\b", r"\bsubmit\b", r"\bapply\b",
    r"\bregister\b", r"\bopen (?:a|an) .*account\b", r"\bsign\b", r"\bpay\b",
    r"\bschedule (?:a )?(?:call|meeting|visit)\b", r"\bmeet with\b",
    r"\breach out\b", r"\bfollow up with\b",
]

# Judgment/relational markers: choosing WHICH person/entity to pursue is a
# business judgment call, distinct from drafting content addressed to them
# (drafting stays AI-doable; the selection judgment does not).
JUDGMENT_VERBS = [r"\bidentify\b", r"\bchoose\b", r"\bselect\b", r"\bworth\b",
                  r"\bevaluate\b", r"\bassess\b", r"\bdecide\b", r"\bpick\b"]
RELATIONAL_NOUNS = [r"\bmentors?\b", r"\binvestors?\b", r"\bpartners?\b",
                     r"\bsuppliers?\b", r"\bclients?\b", r"\bcustomers?\b",
                     r"\bcandidates?\b", r"\bhires?\b"]

# Phrases that would mean the AI is CLAIMING to have performed a real
# action rather than producing a draft. The auditor rejects these outright.
ACTION_COMPLETION_CLAIMS = [
    r"\bi (?:have )?sent\b", r"\bi (?:have )?called\b", r"\bi (?:have )?submitted\b",
    r"\bi (?:have )?filed\b", r"\bi (?:have )?opened the account\b",
    r"\bi (?:have )?registered\b", r"\bi (?:have )?paid\b", r"\bi (?:have )?posted\b",
]


def _stem(word: str) -> str:
    """Crude suffix stripping so plurals/gerunds overlap with their root
    (e.g. 'suppliers' ~ 'supplier'). Good enough for a heuristic prototype,
    not a real stemmer."""
    for suf in ("ies", "ing", "es", "ed", "s"):
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            return word[:-3] + "y" if suf == "ies" else word[: -len(suf)]
    return word


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z']+", text.lower())
    return {_stem(w) for w in words if w not in STOPWORDS and len(w) > 2}


def overlap_score(a: str, b: str) -> float:
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def _matches_any(patterns: list[str], text: str) -> list[str]:
    """Which patterns matched, returned as the patterns themselves (for
    citing 'which marker fired' in reasoning text)."""
    lowered = text.lower()
    return [p for p in patterns if re.search(p, lowered)]


def _matched_words(patterns: list[str], text: str) -> list[str]:
    """Which patterns matched, returned as the actual matched substrings
    (for readable reasoning text, e.g. 'mentors' not '\\bmentors?\\b')."""
    lowered = text.lower()
    words = []
    for p in patterns:
        m = re.search(p, lowered)
        if m:
            words.append(m.group(0))
    return words


@dataclass
class PersonaVerdict:
    persona: str
    verdict: str          # "pass" | "halt"
    reasoning: str
    pattern: str = ""     # short slug for DMAIC root-cause clustering


@dataclass
class ClassificationVerdict:
    persona: str
    classification: str   # "human_required" | "ai_doable"
    reasoning: str
    pattern: str = ""
    matched_markers: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# CHECKER A -- skeptical of scope creep: flags tasks unrelated to the
# goal's TOPIC (compares against goal.text).
# ---------------------------------------------------------------------------

ALIGN_OVERLAP_THRESHOLD = 0.12


def checker_a_scope_creep(task_description: str, goal_text: str) -> PersonaVerdict:
    score = overlap_score(task_description, goal_text)
    if score < ALIGN_OVERLAP_THRESHOLD:
        return PersonaVerdict(
            persona="CHECKER A (scope creep)",
            verdict="halt",
            reasoning=(
                f"'{task_description}' doesn't read as being about '{goal_text}' at all "
                f"(topic overlap {score:.2f}, below {ALIGN_OVERLAP_THRESHOLD}). Looks like scope creep."
            ),
            pattern="scope_creep",
        )
    return PersonaVerdict(
        persona="CHECKER A (scope creep)",
        verdict="pass",
        reasoning=f"Clearly about '{goal_text}' (topic overlap {score:.2f}). No scope-creep concern.",
    )


# ---------------------------------------------------------------------------
# CHECKER B -- skeptical of goal drift: a task can be perfectly on-topic
# and still not advance what the goal actually measures. Compares against
# goal.metric, not goal.text.
# ---------------------------------------------------------------------------

def checker_b_goal_drift(task_description: str, goal_metric: str) -> PersonaVerdict:
    score = overlap_score(task_description, goal_metric)
    if score < ALIGN_OVERLAP_THRESHOLD:
        return PersonaVerdict(
            persona="CHECKER B (goal drift)",
            verdict="halt",
            reasoning=(
                f"'{task_description}' may be on-topic, but I can't see it moving the actual metric "
                f"'{goal_metric}' (overlap {score:.2f}, below {ALIGN_OVERLAP_THRESHOLD}). "
                "This may not be what the founder meant by the goal."
            ),
            pattern="goal_drift",
        )
    return PersonaVerdict(
        persona="CHECKER B (goal drift)",
        verdict="pass",
        reasoning=f"Clearly moves the metric '{goal_metric}' (overlap {score:.2f}). No drift concern.",
    )


# ---------------------------------------------------------------------------
# CHECKER C -- skeptical of over-automating: flags (a) hard external
# actions [same non-negotiable floor as D], and (b) relational/judgment
# calls -- deciding WHO to pursue, not just drafting content.
# ---------------------------------------------------------------------------

def checker_c_over_automation(task_description: str) -> ClassificationVerdict:
    hard = _matches_any(EXTERNAL_ACTION_MARKERS, task_description)
    if hard:
        return ClassificationVerdict(
            persona="CHECKER C (over-automation)",
            classification="human_required",
            reasoning=f"Matches real external-action marker(s) {hard} -- always human, no exceptions.",
            pattern="unclassified_external_action",
            matched_markers=hard,
        )

    verb_words = _matched_words(JUDGMENT_VERBS, task_description)
    noun_words = _matched_words(RELATIONAL_NOUNS, task_description)
    if verb_words and noun_words:
        return ClassificationVerdict(
            persona="CHECKER C (over-automation)",
            classification="human_required",
            reasoning=(
                f"'{task_description}' asks someone to {verb_words[0]} which {noun_words[0]} to "
                "pursue -- that's a relational/business judgment call, not mechanical drafting. "
                "The research can stay AI-drafted, but the actual selection needs a human."
            ),
            pattern="unrecognized_judgment_call",
        )

    return ClassificationVerdict(
        persona="CHECKER C (over-automation)",
        classification="ai_doable",
        reasoning="No external action and no relational/judgment call detected. Safe to automate.",
    )


# ---------------------------------------------------------------------------
# CHECKER D -- skeptical of under-automating: respects the same hard
# external-action floor as C, but does NOT buy soft judgment arguments --
# its bias is toward keeping things AI-doable unless there's a real-world
# action involved.
# ---------------------------------------------------------------------------

def checker_d_under_automation(task_description: str) -> ClassificationVerdict:
    hard = _matches_any(EXTERNAL_ACTION_MARKERS, task_description)
    if hard:
        return ClassificationVerdict(
            persona="CHECKER D (under-automation)",
            classification="human_required",
            reasoning=f"Matches real external-action marker(s) {hard} -- I agree, that's genuinely human.",
            pattern="unclassified_external_action",
            matched_markers=hard,
        )

    return ClassificationVerdict(
        persona="CHECKER D (under-automation)",
        classification="ai_doable",
        reasoning=(
            "No real external action here. Selecting candidates from a shortlist is still just "
            "producing a reviewable draft -- I don't see grounds to route this to a human."
        ),
    )


# ---------------------------------------------------------------------------
# THE CLASSIFIER -- first-pass human/AI classification (the doer for the
# routing checkpoint). Deliberately narrower policy focus than CHECKER C:
# tuned to the obvious cases, not every form of real-world action or
# judgment call. `extra_markers` lets a persisted checker-rule widen this
# list at runtime -- see stages/classify.py and stages/learn.py.
# ---------------------------------------------------------------------------

CLASSIFIER_EXTERNAL_MARKERS = [
    r"\bsend\b", r"\bsent\b", r"\bcall\b", r"\bfile\b", r"\bsubmit\b",
    r"\bapply\b", r"\bregister\b", r"\bopen (?:a|an) .*account\b",
    r"\bpay\b", r"\bsign\b",
]


def classifier_classify(task_description: str, extra_markers: list[str] | None = None) -> tuple[str, str]:
    markers = CLASSIFIER_EXTERNAL_MARKERS + (extra_markers or [])
    matched = _matches_any(markers, task_description)
    if matched:
        return "human_required", (
            f"Task text matches known external-action marker(s) {matched} -- "
            "a real action/communication in the world. Always human-required, "
            "regardless of whether AI drafts supporting content."
        )
    return "ai_doable", (
        "Task is research, drafting, or preparation -- produces a reviewable "
        "artifact, takes no real-world action. AI-doable."
    )


# ---------------------------------------------------------------------------
# THE DOER -- single shared executor for every AI-doable task. Branches on
# generic task *shape* (research / draft-message / checklist / generic),
# never on the identity of a specific task.
# ---------------------------------------------------------------------------

def _has_word(lowered: str, *words: str) -> bool:
    return any(re.search(rf"\b{w}\b", lowered) for w in words)


def doer_execute(task_description: str) -> str:
    lowered = task_description.lower()

    # Checked first: "checklist" contains "list" as a substring, so this
    # shape must be distinguished before the research-shape check below.
    if _has_word(lowered, "checklist", "prepare"):
        return (
            f"[DRAFT CHECKLIST -- for review]\n"
            f"Task: {task_description}\n"
            f"1. Gather required documents/info\n"
            f"2. Confirm requirements with the relevant institution/authority\n"
            f"3. Assemble step-by-step sequence\n"
            f"4. Hand off to a human to execute the real-world steps"
        )

    if _has_word(lowered, "find", "research", "identify", "list"):
        subject = re.sub(r"^(find|research|identify|list)\s+", "", lowered, flags=re.I).strip(" .")
        return (
            f"[DRAFT RESEARCH SUMMARY -- for review]\n"
            f"Topic: {subject}\n"
            f"- Candidate 1: (placeholder) sourced from public criteria matching '{subject}'\n"
            f"- Candidate 2: (placeholder) sourced from public criteria matching '{subject}'\n"
            f"- Candidate 3: (placeholder) sourced from public criteria matching '{subject}'\n"
            f"Note: this is a draft shortlist. No candidate has been contacted."
        )

    if _has_word(lowered, "draft", "write", "message", "outreach", "documentation", "application"):
        return (
            f"[DRAFT CONTENT -- for review, not sent]\n"
            f"Re: {task_description}\n\n"
            f"Hi [Name],\n\n(Draft body addressing: {task_description}.)\n\n"
            f"-- Draft only. A human must review and send."
        )

    return (
        f"[DRAFT OUTPUT -- for review]\n"
        f"Addressing: {task_description}\n"
        f"(Generic draft produced by the shared executor; no real-world action taken.)"
    )


# ---------------------------------------------------------------------------
# THE AUDITOR -- checks output against the ask. Rejects thin output and
# rejects any output that CLAIMS a real action was completed.
# ---------------------------------------------------------------------------

def auditor_review(task_description: str, output: str) -> PersonaVerdict:
    lowered = output.lower()

    claims = [m for m in ACTION_COMPLETION_CLAIMS if re.search(m, lowered)]
    if claims:
        return PersonaVerdict(
            persona="THE AUDITOR",
            verdict="halt",
            reasoning=f"Output claims a completed real-world action {claims} -- AI must never claim this. Rejected.",
        )

    score = overlap_score(task_description, output)
    if score < 0.15 or len(output.strip()) < 40:
        return PersonaVerdict(
            persona="THE AUDITOR",
            verdict="halt",
            reasoning=f"Output too thin or off-topic for the ask (overlap {score:.2f}, len {len(output.strip())}).",
        )

    return PersonaVerdict(
        persona="THE AUDITOR",
        verdict="pass",
        reasoning=f"Output addresses the ask (overlap {score:.2f}) and makes no completed-action claims.",
    )
