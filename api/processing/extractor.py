"""
APEX — LabelSure Declaration Extractor.

Maps OCR text regions to strict Declaration contracts.
"""

import re
from typing import List, Dict
from schemas.declaration import Declaration, DeclarationType, DeclarationStatus

# Simple Regex patterns for demonstration (expandable)
PATTERNS = {
    DeclarationType.MRP: r"(MRP|mrp|Price|price).{0,5}(\d+(?:\.\d{2})?)",
    DeclarationType.NET_QUANTITY: r"(\d{1,4}\s?(g|kg|ml|l|ltr))",
    DeclarationType.MANUFACTURE_OR_PACK_DATE: r"(\d{2}/\d{2}/\d{2,4})",
    DeclarationType.PRODUCT_NAME: r"(?i)(Brand|Name|Product):?\s?([\w\s]+)",
}

def extract_declarations(ocr_results: List[Dict], image_id: str) -> List[Declaration]:
    """Map OCR segments to Declaration models."""
    declarations = []

    for segment in ocr_results:
        text = segment["text"]

        for dtype, pattern in PATTERNS.items():
            match = re.search(pattern, text)
            if match:
                val = match.group(0) if dtype != DeclarationType.MRP else match.group(2)
                declarations.append(Declaration(
                    type=dtype,
                    raw_text=text,
                    normalized_value=val,
                    confidence=segment["confidence"],
                    bbox=segment["bbox"],
                    image_id=image_id,
                    panel="front",
                    status=DeclarationStatus.EXTRACTED
                ))
    return declarations
