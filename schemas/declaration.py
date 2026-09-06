"""Declaration schema — one extracted label field from a product image."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DeclarationType(str, Enum):
    """Legal Metrology declaration types per the Packaged Commodities Rules."""

    PRODUCT_NAME = "PRODUCT_NAME"
    MANUFACTURER = "MANUFACTURER"
    PACKER = "PACKER"
    IMPORTER = "IMPORTER"
    COUNTRY_OF_ORIGIN = "COUNTRY_OF_ORIGIN"
    NET_QUANTITY = "NET_QUANTITY"
    MRP = "MRP"
    MANUFACTURE_OR_PACK_DATE = "MANUFACTURE_OR_PACK_DATE"
    BEST_BEFORE_OR_USE_BY = "BEST_BEFORE_OR_USE_BY"
    CONSUMER_CARE = "CONSUMER_CARE"
    UNIT_SALE_PRICE = "UNIT_SALE_PRICE"
    OTHER_DECLARATION = "OTHER_DECLARATION"


class DeclarationStatus(str, Enum):
    """Processing status of a single declaration extraction."""

    EXTRACTED = "extracted"
    NORMALIZED = "normalized"
    VALIDATED = "validated"
    FAILED = "failed"


class Declaration(BaseModel):
    """
    A single declaration extracted from a product label image.

    Represents one mandatory or optional field that Legal Metrology
    rules require on packaged commodities.
    """

    type: DeclarationType = Field(
        ..., description="The Legal Metrology declaration type."
    )
    raw_text: str = Field(
        ..., description="Verbatim OCR text as read from the label."
    )
    normalized_value: str = Field(
        "", description="Cleaned / standardized value after NLP processing."
    )
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="OCR + NER extraction confidence score.",
    )
    bbox: List[float] = Field(
        default_factory=lambda: [0.0, 0.0, 0.0, 0.0],
        min_length=4,
        max_length=4,
        description="Bounding box [x_min, y_min, x_max, y_max] in pixel coords.",
    )
    image_id: str = Field(
        "", description="Reference to the source image (e.g. IMG-01)."
    )
    panel: str = Field(
        "", description="Label panel where this declaration was found (front, back, side, etc.)."
    )
    status: DeclarationStatus = Field(
        DeclarationStatus.EXTRACTED,
        description="Current processing status of this declaration.",
    )

    model_config = {"json_schema_extra": {"examples": [
        {
            "type": "NET_QUANTITY",
            "raw_text": "Net Wt. 500g",
            "normalized_value": "500 g",
            "confidence": 0.96,
            "bbox": [120, 340, 280, 370],
            "image_id": "IMG-01",
            "panel": "front",
            "status": "normalized",
        }
    ]}}
