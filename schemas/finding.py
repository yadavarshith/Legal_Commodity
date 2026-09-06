"""Finding / evidence schema — one rule evaluation result with evidence chain."""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FindingStatus(str, Enum):
    """Outcome of evaluating one rule against one product."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"
    NOT_APPLICABLE = "N/A"


class EvidenceItem(BaseModel):
    """A single piece of visual / OCR evidence backing a finding."""

    image_id: str = Field(..., description="Source image reference (e.g. IMG-02).")
    bbox: List[float] = Field(
        default_factory=lambda: [0.0, 0.0, 0.0, 0.0],
        min_length=4,
        max_length=4,
        description="Bounding box [x_min, y_min, x_max, y_max].",
    )
    ocr_text: str = Field("", description="OCR text extracted from this region.")


class InspectorDecision(BaseModel):
    """Inspector's final call on a finding — human-in-the-loop."""

    decision: str = Field(
        "pending",
        description="Inspector verdict: pending | confirmed | overridden.",
    )
    comment: str = Field("", description="Inspector's free-text note.")


class Finding(BaseModel):
    """
    Result of evaluating one Legal Metrology rule against a product.

    Design law: AI produces findings; inspectors verify them.
    A FAIL status is a recommendation for review, never a legal
    determination on its own.
    """

    finding_id: str = Field(
        ...,
        pattern=r"^F-\d{4}$",
        description="Unique finding identifier (e.g. F-0001).",
    )
    rule_id: str = Field(
        ...,
        pattern=r"^LM-\d{4}$",
        description="The rule that was evaluated.",
    )
    status: FindingStatus = Field(
        ..., description="Outcome of the rule evaluation."
    )
    description: str = Field(
        ..., description="Human-readable explanation of the finding."
    )
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Visual / OCR evidence supporting this finding.",
    )
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="AI confidence in this finding.",
    )
    rule_version: str = Field(
        "", description="Version of the rule that was applied."
    )
    ai_model_versions: List[str] = Field(
        default_factory=list,
        description="Model versions used (e.g. ['ocr-v2.1', 'ner-v1.3']).",
    )
    inspector: InspectorDecision = Field(
        default_factory=InspectorDecision,
        description="Inspector's human-in-the-loop decision.",
    )

    model_config = {"json_schema_extra": {"examples": [
        {
            "finding_id": "F-0001",
            "rule_id": "LM-0001",
            "status": "FAIL",
            "description": "Product name not found on the label.",
            "evidence": [
                {"image_id": "IMG-02", "bbox": [0, 0, 0, 0], "ocr_text": ""}
            ],
            "confidence": 0.94,
            "rule_version": "1.0.0",
            "ai_model_versions": ["ocr-v2.1", "ner-v1.3"],
            "inspector": {"decision": "pending", "comment": ""},
        }
    ]}}
