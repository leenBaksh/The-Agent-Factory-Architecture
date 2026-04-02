"""
Agent guardrails: PII detection, keyword escalation, and sentiment analysis.

Three input guardrails are attached to the support agent:

  1. pii_guardrail              — detects PII in the customer message; logs a
                                  warning but does NOT block (tripwire=False).
                                  Call mask_pii() before handing text to the agent.

  2. keyword_escalation_guardrail — trips (tripwire=True) when the message
                                  contains legally/financially sensitive words.
                                  The coordinator catches the exception and
                                  escalates automatically.

  3. sentiment_guardrail        — trips when the computed anger/frustration
                                  score exceeds 0.60, triggering an empathetic
                                  auto-escalation response.
"""

import logging
import re

from agents import Agent, GuardrailFunctionOutput, InputGuardrail, RunContextWrapper

logger = logging.getLogger(__name__)


# ── PII patterns ───────────────────────────────────────────────────────────────

_PII_PATTERNS: dict[str, re.Pattern] = {
    "email":       re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
    "phone":       re.compile(
                       r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
                   ),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "ssn":         re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"),
}

_PII_PLACEHOLDERS: dict[str, str] = {
    "email":       "[EMAIL]",
    "phone":       "[PHONE]",
    "credit_card": "[CARD]",
    "ssn":         "[SSN]",
}


def mask_pii(text: str) -> str:
    """Replace all detected PII with labelled placeholders. Safe to log."""
    result = text
    for key, pattern in _PII_PATTERNS.items():
        result = pattern.sub(_PII_PLACEHOLDERS[key], result)
    return result


def detect_pii(text: str) -> dict[str, list[str]]:
    """Return {pii_type: [matches]} for every PII pattern that fires."""
    return {
        key: pattern.findall(text)
        for key, pattern in _PII_PATTERNS.items()
        if pattern.search(text)
    }


# ── Escalation keywords ────────────────────────────────────────────────────────

# User-specified: "refund", "pricing", "legal", "lawsuit"
# Extended with adjacent high-risk terms
_ESCALATION_KEYWORDS: frozenset[str] = frozenset({
    "refund",
    "pricing",
    "legal",
    "lawsuit",
    "lawyer",
    "attorney",
    "sue",
    "suing",
    "court",
    "chargeback",
    "fraud",
    "dispute",
    "regulatory",
    "violation",
    "gdpr",
    "compliance",
})


def find_escalation_keyword(text: str) -> str | None:
    """Return the first matching escalation keyword found in text, else None."""
    lower = text.lower()
    for keyword in _ESCALATION_KEYWORDS:
        if keyword in lower:
            return keyword
    return None


# ── Sentiment analysis ─────────────────────────────────────────────────────────

_ANGRY_WORDS: frozenset[str] = frozenset({
    "angry",
    "furious",
    "frustrated",
    "outraged",
    "unacceptable",
    "terrible",
    "horrible",
    "disgusting",
    "ridiculous",
    "pathetic",
    "useless",
    "garbage",
    "scam",
    "hate",
    "disgusted",
    "incompetent",
    "idiots",
    "waste of time",
    "rip off",
    "never again",
    "appalling",
    "awful",
    "disaster",
})

_SENTIMENT_ESCALATION_THRESHOLD: float = 0.60


def sentiment_score(text: str) -> float:
    """
    Return a float 0.0–1.0 representing anger/negativity.

    Three weighted signals:
      • Angry keyword density  — weight 0.50
        (3+ angry words → maximum contribution)
      • All-caps word ratio    — weight 0.30
        (shouting in text)
      • Excessive punctuation  — weight 0.20
        (5+ ! or ? → maximum contribution)
    """
    lower = text.lower()
    words = text.split()

    # Signal 1: angry keyword density
    angry_hits = sum(1 for kw in _ANGRY_WORDS if kw in lower)
    kw_score = min(1.0, angry_hits / 3.0)

    # Signal 2: all-caps words (len ≥ 3, excludes abbreviations like "OK")
    if words:
        caps_words = sum(1 for w in words if len(w) >= 3 and w.isupper())
        caps_score = min(1.0, caps_words / max(len(words) * 0.25, 1))
    else:
        caps_score = 0.0

    # Signal 3: excessive punctuation
    punct_score = min(1.0, (text.count("!") + text.count("?")) / 5.0)

    return round(0.50 * kw_score + 0.30 * caps_score + 0.20 * punct_score, 3)


# ── Guardrail functions ────────────────────────────────────────────────────────


async def _pii_guardrail_fn(
    ctx: RunContextWrapper,
    agent: Agent,
    input: str,
) -> GuardrailFunctionOutput:
    """
    Detect PII in the customer message.

    Non-blocking (tripwire=False): logs the PII types found and stores
    the masked copy in output_info for the coordinator to use.
    The raw content is NEVER logged.
    """
    found = detect_pii(input)
    if found:
        logger.warning(
            "PII detected in inbound message — type(s): %s. "
            "Content will be masked before logging/storage.",
            list(found.keys()),
        )
    return GuardrailFunctionOutput(
        output_info={
            "pii_detected": bool(found),
            "pii_types": list(found.keys()),
            "masked_content": mask_pii(input),
        },
        tripwire_triggered=False,
    )


async def _keyword_escalation_fn(
    ctx: RunContextWrapper,
    agent: Agent,
    input: str,
) -> GuardrailFunctionOutput:
    """
    Detect legally/financially sensitive keywords.

    Blocking (tripwire=True): the agent is NOT invoked; the coordinator
    catches InputGuardrailTripwireTriggered and auto-escalates.
    """
    keyword = find_escalation_keyword(input)
    triggered = keyword is not None
    if triggered:
        logger.info(
            "Keyword escalation guardrail triggered: keyword=%r", keyword
        )
    return GuardrailFunctionOutput(
        output_info={
            "reason": "keyword_escalation",
            "keyword": keyword,
        },
        tripwire_triggered=triggered,
    )


async def _sentiment_guardrail_fn(
    ctx: RunContextWrapper,
    agent: Agent,
    input: str,
) -> GuardrailFunctionOutput:
    """
    Score the anger/frustration level of the message.

    Blocking (tripwire=True) when score ≥ 0.60: the coordinator catches
    InputGuardrailTripwireTriggered and sends an empathetic escalation response.
    """
    score = sentiment_score(input)
    triggered = score >= _SENTIMENT_ESCALATION_THRESHOLD
    if triggered:
        logger.info(
            "Sentiment escalation guardrail triggered: score=%.3f (threshold=%.2f)",
            score,
            _SENTIMENT_ESCALATION_THRESHOLD,
        )
    return GuardrailFunctionOutput(
        output_info={
            "reason": "high_anger_sentiment",
            "score": score,
            "threshold": _SENTIMENT_ESCALATION_THRESHOLD,
        },
        tripwire_triggered=triggered,
    )


# ── InputGuardrail instances ───────────────────────────────────────────────────

pii_guardrail = InputGuardrail(guardrail_function=_pii_guardrail_fn)
keyword_escalation_guardrail = InputGuardrail(guardrail_function=_keyword_escalation_fn)
sentiment_guardrail = InputGuardrail(guardrail_function=_sentiment_guardrail_fn)
