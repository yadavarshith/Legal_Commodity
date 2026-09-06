"""Inspection contract schema — the top-level document for one inspection session."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from schemas.declaration import Declaration
from schemas.finding import Finding


class InspectionStatus(str, Enum):
    """Overall inspection lifecycle status."""

    DRAFT = "draft"
    PROCESSING = "processing"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ImageQuality(str, Enum):
    """Image quality assessment result."""

    PASS = "pass"
    MARGINAL = "marginal"
    FAIL = "fail"


class InspectionImage(BaseModel):
    """One image submitted for an inspection."""

    id: str = Field(..., description="Image identifier (e.g. IMG-01).")
    path: str = Field(..., description="Storage path or URI for the image.")
    panel: str = Field(
        "front", description="Which label panel (front, back, side, top, bottom)."
    )
    quality: ImageQuality = Field(
        ImageQuality.PASS, description="Quality gate result."
    )


class ProductContext(BaseModel):
    """Product metadata supplied by the inspector or inferred."""

    category: str = Field("", description="Product category (food, cosmetics, etc.).")
    package_type: str = Field("", description="Package type (bottle, box, sachet, etc.).")
    import_status: str = Field(
        "", description="Import status (domestic, imported, etc.)."
    )


class InspectionTrace(BaseModel):
    """Ordered pipeline steps executed during this inspection."""

    steps: List[str] = Field(
        default_factory=lambda: [
            "quality", "ocr", "extract", "context", "rules", "review"
        ],
        description="Pipeline steps in execution order.",
    )


class Inspection(BaseModel):
    """
    Top-level inspection document — the complete record of one
    product-label compliance check.

    Ties together images, extracted declarations, applied rules,
    findings, and the inspector's final review.
    """

    inspection_id: str = Field(
        ...,
        pattern=r"^INS-\d{3,}$",
        description="Unique inspection identifier (e.g. INS-001).",
    )
    images: List[InspectionImage] = Field(
        default_factory=list, description="Submitted label images."
    )
    product_context: ProductContext = Field(
        default_factory=ProductContext,
        description="Product category and packaging metadata.",
    )
    declarations: List[Declaration] = Field(
        default_factory=list,
        description="Extracted declarations from OCR + NER.",
    )
    rule_version: str = Field(
        "", description="Rule corpus version applied to this inspection."
    )
    findings: List[Finding] = Field(
        default_factory=list,
        description="Rule evaluation results.",
    )
    overall_status: InspectionStatus = Field(
        InspectionStatus.REVIEW,
        description="Current inspection lifecycle status.",
    )
    trace: InspectionTrace = Field(
        default_factory=InspectionTrace,
        description="Pipeline execution trace for auditability.",
    )

    model_config = {"json_schema_extra": {"examples": [
        {
            "inspection_id": "INS-001",
            "images": [
                {"id": "IMG-01", "path": "/uploads/ins-001/front.jpg", "panel": "front", "quality": "pass"}
            ],
            "product_context": {"category": "food", "package_type": "box", "import_status": "domestic"},
            "declarations": [],
            "rule_version": "1.0.0",
            "findings": [],
            "overall_status": "review",
            "trace": {"steps": ["quality", "ocr", "extract", "context", "rules", "review"]},
        }
    ]}}
