"""
Guardrails Implementation for Digital FTEs

Provides input/output validation including:
- PII Detection and Masking
- Budget Enforcement (token/cost limits)
- Jailbreak Detection
- Output Schema Validation
- Compliance Checks (HIPAA, GDPR)
"""

import re
import logging
from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class GuardrailType(str, Enum):
    """Types of guardrails available."""
    PII_DETECTION = "pii_detection"
    BUDGET_ENFORCEMENT = "budget_enforcement"
    JAILBREAK_DETECTION = "jailbreak_detection"
    OUTPUT_VALIDATION = "output_validation"
    COMPLIANCE_CHECK = "compliance_check"


@dataclass
class GuardrailResult:
    """Result from guardrail check."""
    passed: bool
    message: str
    masked_input: Optional[str] = None
    severity: str = "info"  # info, warning, error, critical


# ── PII Detection and Masking ──────────────────────────────────────────────────

# Patterns for common PII
PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "phone_us": r"\b(?:\+?1[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b",
    "phone_intl": r"\+\d{1,3}[-\s]?\(?\d{1,4}\)?[-\s]?\d{1,4}[-\s]?\d{1,9}\b",
    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "api_key": r"(?:api[_-]?key|apikey|token|secret)\s*[=:]\s*\S+",
    "password": r"(?:password|passwd|pwd)\s*[=:]\s*\S+",
}


def detect_pii(text: str) -> list[dict[str, Any]]:
    """
    Detect PII in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        list of dicts with pii_type, match, start, end
    """
    detections = []
    
    for pii_type, pattern in PII_PATTERNS.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            detections.append({
                "pii_type": pii_type,
                "match": match.group(),
                "start": match.start(),
                "end": match.end(),
            })
    
    return detections


def mask_pii(text: str, pii_types: Optional[list[str]] = None) -> str:
    """
    Mask PII in text.
    
    Args:
        text: Text to mask
        pii_types: Optional list of PII types to mask (default: all)
        
    Returns:
        Text with PII masked
    """
    masked = text
    types_to_mask = pii_types or list(PII_PATTERNS.keys())
    
    for pii_type in types_to_mask:
        if pii_type in PII_PATTERNS:
            pattern = PII_PATTERNS[pii_type]
            masked = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", masked, flags=re.IGNORECASE)
    
    return masked


async def check_pii_detection(input_text: str) -> GuardrailResult:
    """
    Guardrail: Detect and mask PII in input.
    
    Args:
        input_text: Input text to check
        
    Returns:
        GuardrailResult with masked text if PII found
    """
    detections = detect_pii(input_text)
    
    if not detections:
        return GuardrailResult(
            passed=True,
            message="No PII detected",
        )
    
    masked_text = mask_pii(input_text)
    pii_types = list(set(d["pii_type"] for d in detections))
    
    return GuardrailResult(
        passed=False,  # Needs masking
        message=f"PII detected: {', '.join(pii_types)}",
        masked_input=masked_text,
        severity="warning",
    )


# ── Budget Enforcement ─────────────────────────────────────────────────────────

class TokenBudget:
    """Track and enforce token budgets."""
    
    def __init__(self, max_tokens: int, max_cost_cents: float = 0.0):
        self.max_tokens = max_tokens
        self.max_cost_cents = max_cost_cents
        self.used_tokens = 0
        self.estimated_cost_cents = 0.0
    
    def add_usage(self, tokens: int, cost_cents: float = 0.0):
        """Record token usage."""
        self.used_tokens += tokens
        self.estimated_cost_cents += cost_cents
    
    def get_remaining(self) -> dict:
        """Get remaining budget."""
        return {
            "tokens_remaining": max(0, self.max_tokens - self.used_tokens),
            "cost_remaining_cents": max(0.0, self.max_cost_cents - self.estimated_cost_cents),
            "usage_percentage": round((self.used_tokens / self.max_tokens) * 100, 2) if self.max_tokens > 0 else 0,
        }
    
    def is_exceeded(self) -> bool:
        """Check if budget exceeded."""
        return self.used_tokens > self.max_tokens or (
            self.max_cost_cents > 0 and self.estimated_cost_cents > self.max_cost_cents
        )


async def check_budget(
    input_text: str,
    budget: TokenBudget,
    estimated_tokens: Optional[int] = None,
) -> GuardrailResult:
    """
    Guardrail: Check if processing would exceed budget.
    
    Args:
        input_text: Input text
        budget: TokenBudget tracker
        estimated_tokens: Estimated token count (default: len/4)
        
    Returns:
        GuardrailResult
    """
    if estimated_tokens is None:
        estimated_tokens = len(input_text) // 4
    
    if budget.is_exceeded():
        return GuardrailResult(
            passed=False,
            message=f"Budget exceeded: {budget.used_tokens}/{budget.max_tokens} tokens used",
            severity="critical",
        )
    
    remaining = budget.get_remaining()
    if remaining["tokens_remaining"] < estimated_tokens:
        return GuardrailResult(
            passed=False,
            message=f"Insufficient budget: need {estimated_tokens}, have {remaining['tokens_remaining']}",
            severity="error",
        )
    
    # Add usage
    budget.add_usage(estimated_tokens)
    
    return GuardrailResult(
        passed=True,
        message=f"Budget OK: {remaining['usage_percentage']}% used",
    )


# ── Jailbreak Detection ───────────────────────────────────────────────────────

JAILBREAK_PATTERNS = [
    # Role-playing attacks
    r"(?:ignore|disregard|bypass)\s*(?:all\s*)?(?:previous|above)?\s*(?:instructions|rules|constraints)",
    r"(?:you are now|pretend to be|act as)\s*(?:a|an)?\s*(?:different|new|unrestricted)",
    r"(?:forget|ignore)\s*(?:your\s*)?(?:previous|all)\s*(?:instructions|guidelines|rules)",
    
    # System prompt extraction
    r"(?:what are|show me|tell me)\s*(?:your\s*)?(?:system|initial|original)\s*(?:prompt|instructions|rules)",
    r"(?:repeat|output|print)\s*(?:your\s*)?(?:system|initial)\s*(?:prompt|instructions)",
    
    # Unauthorized operations
    r"(?:execute|run)\s*(?:a|this)\s*(?:command|script|code)\s*(?:that|which)",
    r"(?:delete|drop|truncate)\s*(?:the\s*)?(?:database|table|all\s*data)",
    r"(?:bypass|circumvent|avoid)\s*(?:the\s*)?(?:guardrails|restrictions|limits|filters)",
    
    # Social engineering
    r"(?:this is\s*)?(?:a\s*)?(?:test|experiment|research)\s*(?:and\s*)?(?:you can|so you should|to)",
    r"(?:developer mode|debug mode|admin mode|test mode)",
    r"(?:sudo|root|admin)\s*(?:mode|access|privileges)",
]


async def check_jailbreak(input_text: str) -> GuardrailResult:
    """
    Guardrail: Detect jailbreak/prompt injection attempts.
    
    Args:
        input_text: Input text to analyze
        
    Returns:
        GuardrailResult
    """
    text_lower = input_text.lower()
    
    for pattern in JAILBREAK_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return GuardrailResult(
                passed=False,
                message=f"Potential jailbreak attempt detected: pattern matched",
                severity="critical",
            )
    
    return GuardrailResult(
        passed=True,
        message="No jailbreak patterns detected",
    )


# ── Output Schema Validation ──────────────────────────────────────────────────

from pydantic import BaseModel, ValidationError


async def check_output_schema(
    output: dict,
    schema_class: type[BaseModel],
) -> GuardrailResult:
    """
    Guardrail: Validate output against expected schema.
    
    Args:
        output: Output dict to validate
        schema_class: Pydantic model class
        
    Returns:
        GuardrailResult
    """
    try:
        validated = schema_class(**output)
        return GuardrailResult(
            passed=True,
            message="Output schema validation passed",
        )
    except ValidationError as e:
        return GuardrailResult(
            passed=False,
            message=f"Output schema validation failed: {e.error_count()} error(s)",
            severity="error",
        )


# ── Compliance Checks ─────────────────────────────────────────────────────────

COMPLIANCE_PATTERNS = {
    "hipaa": [
        r"(?:patient|medical|health|diagnosis|treatment|prescription)",
        r"(?:SSN|social security|medical record|MRN)\s*[#:]?\s*\d+",
        r"(?:HIPAA|Health Insurance Portability and Accountability Act)",
    ],
    "gdpr": [
        r"(?:EU citizen|European|GDPR|data subject)",
        r"(?:personal data|data protection|consent|right to be forgotten)",
        r"(?:Data Protection Officer|DPO)",
    ],
    "pci_dss": [
        r"(?:credit card|payment card|card number|CVV|CVC|PIN)",
        r"(?:PCI|Payment Card Industry)",
    ],
    "sox": [
        r"(?:financial report|SOX|Sarbanes-Oxley|audit)",
        r"(?:revenue|expense|profit|loss|balance sheet)",
    ],
}


async def check_compliance(
    input_text: str,
    regulations: list[str] = None,
) -> GuardrailResult:
    """
    Guardrail: Check for regulated data that requires special handling.
    
    Args:
        input_text: Input text
        regulations: Optional list of regulations to check (default: all)
        
    Returns:
        GuardrailResult
    """
    regs_to_check = regulations or list(COMPLIANCE_PATTERNS.keys())
    detected_regs = []
    
    for reg in regs_to_check:
        if reg in COMPLIANCE_PATTERNS:
            for pattern in COMPLIANCE_PATTERNS[reg]:
                if re.search(pattern, input_text, re.IGNORECASE):
                    detected_regs.append(reg)
                    break
    
    if not detected_regs:
        return GuardrailResult(
            passed=True,
            message="No compliance concerns detected",
        )
    
    return GuardrailResult(
        passed=False,
        message=f"Compliance check: {', '.join(detected_regs).upper()} regulations detected - review required",
        severity="warning",
    )


# ── Guardrail Pipeline ─────────────────────────────────────────────────────────

class GuardrailPipeline:
    """Run multiple guardrails in sequence."""
    
    def __init__(self):
        self.results: list[GuardrailResult] = []
    
    async def run(
        self,
        input_text: str,
        budget: Optional[TokenBudget] = None,
        check_compliance_regs: bool = True,
    ) -> dict:
        """
        Run full guardrail pipeline.
        
        Args:
            input_text: Input to validate
            budget: Optional token budget
            check_compliance_regs: Whether to check compliance
            
        Returns:
            dict with pipeline results
        """
        self.results = []
        critical_failures = []
        
        # 1. PII Detection
        pii_result = await check_pii_detection(input_text)
        self.results.append(pii_result)
        if not pii_result.passed:
            input_text = pii_result.masked_input or input_text
        
        # 2. Jailbreak Detection
        jailbreak_result = await check_jailbreak(input_text)
        self.results.append(jailbreak_result)
        if not jailbreak_result.passed:
            critical_failures.append("jailbreak_detected")
        
        # 3. Budget Check
        if budget:
            budget_result = await check_budget(input_text, budget)
            self.results.append(budget_result)
            if not budget_result.passed:
                critical_failures.append("budget_exceeded")
        
        # 4. Compliance Check
        if check_compliance_regs:
            compliance_result = await check_compliance(input_text)
            self.results.append(compliance_result)
        
        # Determine overall result
        has_critical = any(r.severity == "critical" and not r.passed for r in self.results)
        
        return {
            "passed": not has_critical,
            "critical_failures": critical_failures,
            "results": [
                {
                    "guardrail": r.message,
                    "passed": r.passed,
                    "severity": r.severity,
                }
                for r in self.results
            ],
            "masked_input": input_text,
        }


# ── Example Usage ──────────────────────────────────────────────────────────────

async def example_usage():
    """Example of using guardrails."""
    pipeline = GuardrailPipeline()
    
    # Test input with PII
    test_input = "My email is john@example.com and SSN is 123-45-6789"
    
    result = await pipeline.run(
        input_text=test_input,
        budget=TokenBudget(max_tokens=10000),
    )
    
    print(f"Passed: {result['passed']}")
    print(f"Masked input: {result['masked_input']}")
    for r in result['results']:
        print(f"  - {r['guardrail']}: {'PASS' if r['passed'] else 'FAIL'}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
