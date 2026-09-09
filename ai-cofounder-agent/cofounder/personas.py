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
  - THE SKEPTIC    : align-checker -- distrusts decomposition by default
  - THE INSPECTOR  : routing-checker -- a rules-lawyer, not a strategist
  - THE DOER       : single shared executor for all AI-doable tasks
  - THE AUDITOR    : checks output against the ask, not a rubber stamp
"""
from __future__ import annotations

import re
from dataclasses import dataclass

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "with",
    "our", "we", "will", "is", "are", "be", "at", "by", "from", "that",
    "this", "as", "it", "its", "into", "about", "up", "out", "within",
}

# Verbs/phrases that mean "this touches the real world" -- per the spec,
# any task carrying one of these is ALWAYS human-required, even if an AI
# drafted the underlying content.
EXTERNAL_ACTION_MARKERS = [
    r"\bsend\b", r"\bsent\b", r"\bemail\b(?!.*draft)", r"\bcall\b", r"\bcontact\b",
    r"\bpost\b", r"\bpublish\b", r"\bfile\b", r"\bsubmit\b", r"\bapply\b",
    r"\bregister\b", r"\bopen (?:a|an) .*account\b", r"\bsign\b", r"\bpay\b",
    r"\bschedule (?:a )?(?:call|meeting|visit)\b", r"\bmeet with\b",
    r"\breach out\b", r"\bfollow up with\b",
]

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


@dataclass
class PersonaVerdict:
    persona: str
    verdict: str          # "pass" | "halt"
    reasoning: str


# ---------------------------------------------------------------------------
# THE SKEPTIC -- align-checker (distinctly skeptical: assumes mismatch
# until the task proves otherwise via shared vocabulary with its goal)
# ---------------------------------------------------------------------------

ALIGN_OVERLAP_THRESHOLD = 0.12


def skeptic_check_task(task_description: str, goal_text: str, goal_metric: str) -> PersonaVerdict:
    score = max(overlap_score(task_description, goal_text), overlap_score(task_description, goal_metric))
    if score < ALIGN_OVERLAP_THRESHOLD:
        return PersonaVerdict(
            persona="THE SKEPTIC (align-checker)",
            verdict="halt",
            reasoning=(
                f"I don't see how '{task_description}' advances the goal '{goal_text}'. "
                f"Vocabulary overlap is {score:.2f}, below my {ALIGN_OVERLAP_THRESHOLD} bar. "
                "I'm not dropping or rewriting it myself -- flagging for the founder."
            ),
        )
    return PersonaVerdict(
        persona="THE SKEPTIC (align-checker)",
        verdict="pass",
        reasoning=f"Task ties back to '{goal_text}' (overlap {score:.2f}). No objection.",
    )


# ---------------------------------------------------------------------------
# THE INSPECTOR -- routing-checker. Differently prompted from the Skeptic:
# not concerned with goal alignment at all, only with one hard rule --
# real external action/communication is always human-required.
# ---------------------------------------------------------------------------

def inspector_check_classification(task_description: str, classification: str) -> PersonaVerdict:
    matched = [m for m in EXTERNAL_ACTION_MARKERS if re.search(m, task_description.lower())]
    if classification == "ai_doable" and matched:
        return PersonaVerdict(
            persona="THE INSPECTOR (routing-checker)",
            verdict="halt",
            reasoning=(
                f"Classification says AI-doable, but the task text matches external-action marker(s) "
                f"{matched}. Policy: any real external action or communication is ALWAYS human-required, "
                "even if AI drafted the content. Disagreeing with the classifier -- flagging, not fixing."
            ),
        )
    return PersonaVerdict(
        persona="THE INSPECTOR (routing-checker)",
        verdict="pass",
        reasoning=f"No external-action markers conflicting with classification '{classification}'.",
    )


# ---------------------------------------------------------------------------
# THE CLASSIFIER -- decides human-required vs ai-doable, with a reason.
# Deliberately narrower policy focus than THE INSPECTOR below: it's tuned
# to catch the obvious cases (send/file/pay/register/...), not every form
# of real-world action. That gap is intentional and is exactly what THE
# INSPECTOR (a differently-prompted second checker) exists to catch --
# see routing_check.
# ---------------------------------------------------------------------------

CLASSIFIER_EXTERNAL_MARKERS = [
    r"\bsend\b", r"\bsent\b", r"\bcall\b", r"\bfile\b", r"\bsubmit\b",
    r"\bapply\b", r"\bregister\b", r"\bopen (?:a|an) .*account\b",
    r"\bpay\b", r"\bsign\b",
]


def classifier_classify(task_description: str) -> tuple[str, str]:
    lowered = task_description.lower()
    matched = [m for m in CLASSIFIER_EXTERNAL_MARKERS if re.search(m, lowered)]
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
