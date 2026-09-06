"""
APEX — LabelSure Product Context Classifier.
"""

from typing import List
from schemas.declaration import Declaration, DeclarationType
from schemas.inspection import ProductContext

def classify_context(declarations: List[Declaration]) -> ProductContext:
    """Determine inspection metadata from extracted labels."""
    context = ProductContext(category="unknown", package_type="unknown", import_status="domestic")

    # Simple keyword heuristics
    text_blob = " ".join([d.raw_text.lower() for d in declarations])

    if "food" in text_blob or "veg" in text_blob:
        context.category = "food"
    if "imported" in text_blob or "manufactured by" in text_blob:
        context.import_status = "imported" if "imported" in text_blob else "domestic"

    return context
