"""Rule configuration schema — one versioned Legal Metrology rule."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RuleSeverity(str, Enum):
    """How critical a rule violation is."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class ValidationType(str, Enum):
    """Kind of validation the rule engine runs."""

    PRESENCE = "presence"
    FORMAT = "format"
    RANGE = "range"
    CROSS_FIELD = "cross_field"
    CUSTOM = "custom"


class RuleApplicability(BaseModel):
    """When / to what product categories this rule applies."""

    category: str = Field(
        ..., description="Product category (e.g. 'food', 'cosmetics', 'all')."
    )
    conditions: List[str] = Field(
        default_factory=list,
        description="Additional applicability conditions (e.g. 'imported', 'weight > 10kg').",
    )


class RuleValidation(BaseModel):
    """How the rule engine should check this rule."""

    type: ValidationType = Field(
        ..., description="Validation strategy."
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy-specific parameters.",
    )


class RuleConfig(BaseModel):
    """
    A single Legal Metrology rule, versioned and hot-reloadable.

    Rule IDs follow the pattern LM-XXXX.  Each rule references the
    exact DCA clause it encodes and carries validity dates so the
    engine can apply the correct rule set for any inspection date.
    """

    rule_id: str = Field(
        ...,
        pattern=r"^LM-\d{4}$",
        description="Unique rule identifier (e.g. LM-0001).",
    )
    rule_version: str = Field(
        ..., description="Semantic version of this rule definition."
    )
    clause_reference: str = Field(
        ..., description="DCA / Legal Metrology Act clause (e.g. 'Rule 6(1)(a)')."
    )
    requirement: str = Field(
        ..., description="Human-readable statement of what the rule requires."
    )
    applicability: RuleApplicability = Field(
        ..., description="Product categories and conditions where this rule applies."
    )
    validation: RuleValidation = Field(
        ..., description="Validation type and parameters for the rule engine."
    )
    severity: RuleSeverity = Field(
        ..., description="Violation severity level."
    )
    effective_from: str = Field(
        ..., description="ISO-8601 date when this rule becomes effective."
    )
    effective_to: Optional[str] = Field(
        None, description="ISO-8601 date when this rule expires (null = still active)."
    )
    source: str = Field(
        "verified DCA rule document",
        description="Provenance of this rule definition.",
    )

    model_config = {"json_schema_extra": {"examples": [
        {
            "rule_id": "LM-0001",
            "rule_version": "1.0.0",
            "clause_reference": "Rule 6(1)(a)",
            "requirement": "Every package must bear the name of the commodity.",
            "applicability": {"category": "all", "conditions": []},
            "validation": {"type": "presence", "parameters": {"field": "PRODUCT_NAME"}},
            "severity": "critical",
            "effective_from": "2011-01-01",
            "effective_to": None,
            "source": "verified DCA rule document",
        }
    ]}}
