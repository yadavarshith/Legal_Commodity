"""
APEX — LabelSure Declaration Extractor.
Maps OCR text regions to strict Declaration contracts for all Legal Metrology statutory fields.
Designed to handle real OCR text (with potential typos, mixed case, noisy characters).
"""

import re
from typing import List, Dict, Optional
from schemas.declaration import Declaration, DeclarationType, DeclarationStatus

# ──────────────────────────────────────────────────────────────────
# Comprehensive Regex patterns for Legal Metrology PCR 2011 fields
# Ordered by specificity — more specific patterns first
# ──────────────────────────────────────────────────────────────────

PATTERNS = {
    DeclarationType.PRODUCT_NAME: [
        r"(?i)(?:Brand|Product\s*Name|Name\s*of\s*(?:the\s*)?(?:Product|Commodity|Item))[\s:]+(.+)",
        r"(?i)(?:Product|Commodity|Item)\s*:\s*(.+)",
    ],
    DeclarationType.MANUFACTURER: [
        r"(?i)(?:Mfg\.?\s*(?:&|and)?\s*(?:Mkd|Mktd|Packed|Pkd)\.?\s*(?:By)?|Manufactured\s*(?:By|&\s*Packed\s*By)|Mfg\.?\s*By|Packed\s*By|Packer|Importer|Marketed\s*By|Distributed\s*By)[\s:]+(.+)",
        r"(?i)(?:Manufacturer|Packer\s*Address|Regd\.?\s*(?:Office|Off))[\s:]+(.+)",
        r"(?i).+(?:Pvt\.?\s*Ltd\.?|Limited|Co(?:\.|operative)?|Inc\.?|Corp(?:oration)?|Industries|Refineries|Labs|Holdings)\b.+",
    ],
    DeclarationType.NET_QUANTITY: [
        r"(?i)(?:Net\s*(?:Qty|Wt|Weight|Quantity|Vol|Volume|Content))[\s:.]*(\d+(?:[.,]\d+)?\s*(?:g|gm|gms|kg|kgs|ml|mL|l|ltr|litres?|liters?|oz|fl\.?\s*oz))\b",
        r"(?i)(?:Contents?|Quantity|Wt\.?)[\s:.]*(\d+(?:[.,]\d+)?\s*(?:g|gm|kg|ml|mL|l|ltr))\b",
        r"\b(\d+(?:[.,]\d+)?\s*(?:g|gm|kg|ml|mL|l|ltr|oz))\b",
    ],
    DeclarationType.MRP: [
        r"(?i)(?:M\.?\s*R\.?\s*P\.?|Maximum\s*Retail\s*Price|Max\.?\s*Price)[\s:.]*(?:Rs\.?|INR|₹)?\s*(\d+(?:[.,]\d{1,2})?)",
        r"(?i)(?:Rs\.?|INR|₹)\s*(\d+(?:[.,]\d{1,2})?)\s*(?:\(?\s*(?:Incl|incl))?",
        r"(?i)(?:Price|MRP)[\s:.]*(\d+(?:\.\d{1,2})?)",
    ],
    DeclarationType.MANUFACTURE_OR_PACK_DATE: [
        r"(?i)(?:Mfg\.?\s*(?:/\s*)?(?:Pack(?:ing|ed)?)?\.?\s*Date|Pack(?:ed|ing)?\s*(?:on|Date)|Date\s*of\s*(?:Mfg|Manufacture|Packing)|Mfg\.?\s*Dt\.?)[\s:.]*(\d{1,2}[\s/\-\.]\s*\d{1,2}[\s/\-\.]\s*\d{2,4}|\w+[\s/\-]\d{2,4}|\d{1,2}[\s/\-]\d{2,4})",
        r"(?i)(?:Mfg|Pkd|Packed)[\s:.]*(\d{1,2}/\d{2,4})",
    ],
    DeclarationType.BEST_BEFORE_OR_USE_BY: [
        r"(?i)(?:Best\s*Before|Use\s*By|Expiry\s*Date|Exp\.?\s*Date|BB|Exp)[\s:.]*(.+?)(?:\s*$|\s*from)",
        r"(?i)Best\s*Before\s+(\d+\s*(?:Months?|Days?|Years?|Yrs?))",
    ],
    DeclarationType.CONSUMER_CARE: [
        r"(?i)(?:Consumer\s*Care|Customer\s*Care|Helpline|Toll\s*Free|Care\s*(?:Email|Line)|Feedback|Contact\s*Us|For\s*(?:Queries|Complaints))[\s:.]*(.+)",
        r"[\w\.\-]+@[\w\.\-]+\.\w{2,}",
        r"\b1800[\s\-]?\d{2,4}[\s\-]?\d{3,4}\b",
    ],
    DeclarationType.COUNTRY_OF_ORIGIN: [
        r"(?i)(?:Country\s*of\s*Origin|Origin|Made\s*[Ii]n|Product\s*of|Imported\s*[Ff]rom)[\s:.]*(.+)",
        r"(?i)\b(India|China|USA|United\s*States|UK|Germany|Switzerland|France|Japan|South\s*Korea|Thailand|Vietnam|Indonesia|Malaysia|Bangladesh|Sri\s*Lanka|Italy|Spain|Australia|Canada|Brazil|Mexico|Turkey|Taiwan|Netherlands|Belgium|Singapore|Nepal)\b",
    ],
}

# Additional fields that can appear on Indian packaged commodities
EXTRA_PATTERNS = {
    "FSSAI_LICENSE": [
        r"(?i)(?:FSSAI|Lic|License|Licence)\s*(?:No\.?|Number)?[\s:.]*(\d{10,14})",
        r"\b(\d{10,14})\b",  # FSSAI license numbers are 14 digits
    ],
    "BATCH_NUMBER": [
        r"(?i)(?:Batch|Lot)\s*(?:No\.?|Number|#)?[\s:.]*([A-Z0-9\-/]+)",
    ],
    "INGREDIENTS": [
        r"(?i)(?:Ingredients?|Contains?)[\s:.]+(.+)",
    ],
    "ALLERGEN": [
        r"(?i)(?:Allergen|Allergy)\s*(?:Info|Information|Warning|Advice)?[\s:.]*(.+)",
        r"(?i)(?:Contains?|May\s*Contain)[\s:]*(.+?(?:nut|milk|soy|wheat|egg|gluten|shellfish|fish).+)",
    ],
}


def clean_extracted_value(dtype: DeclarationType, raw_text: str, match: re.Match) -> str:
    """Extract clean, normalized value from regex match without prefix clutter."""
    if match.groups():
        val = match.group(1).strip()
    else:
        val = match.group(0).strip()

    # Clean common prefixes
    prefixes = [
        r"(?i)^(?:Brand\s*/?\s*)?Product\s*(?:Name)?\s*:\s*",
        r"(?i)^(?:Name|Brand|Item)\s*:\s*",
        r"(?i)^Net\s*(?:Qty|Wt|Weight|Quantity|Vol|Volume)\s*[:.]\s*",
        r"(?i)^M\.?R\.?P\.?\s*(?:Rs\.?|INR|₹)?\s*[:.]*\s*",
        r"(?i)^(?:Rs\.?|INR|₹)\s*",
        r"(?i)^Manufactured?\s*(?:By|&\s*Packed\s*By)?\s*[:.]\s*",
        r"(?i)^(?:Mfg|Pack(?:ed|ing)?)\s*(?:/\s*Pack)?\s*Date\s*[:.]\s*",
        r"(?i)^Consumer\s*Care\s*[:.]\s*",
        r"(?i)^(?:Country\s*of\s*)?Origin\s*[:.]\s*",
        r"(?i)^(?:Best\s*Before|Use\s*By|Exp(?:iry)?\s*Date)\s*[:.]\s*",
        r"(?i)^Made\s*[Ii]n\s*[:.]\s*",
    ]
    for p in prefixes:
        val = re.sub(p, "", val).strip()

    # Remove trailing noise characters
    val = re.sub(r"[\s|]+$", "", val).strip()
    # Remove leading/trailing punctuation noise
    val = val.strip(".:;,- ")

    return val if val and len(val) >= 2 else ""


def extract_declarations(ocr_results: List[Dict], image_id: str) -> List[Declaration]:
    """
    Map OCR text segments to Declaration models.
    Iterates all OCR blocks and matches against Legal Metrology patterns.
    Also concatenates adjacent short blocks for better multi-line field matching.
    """
    declarations = []
    found_types = set()

    if not ocr_results:
        return declarations

    # First pass: Try matching individual OCR blocks
    for segment in ocr_results:
        text = segment.get("text", "").strip()
        if not text or len(text) < 2:
            continue

        for dtype, pattern_list in PATTERNS.items():
            if dtype in found_types:
                continue

            for pattern in pattern_list:
                try:
                    match = re.search(pattern, text)
                except re.error:
                    continue

                if match:
                    norm_val = clean_extracted_value(dtype, text, match)
                    if norm_val and len(norm_val) >= 2:
                        declarations.append(Declaration(
                            type=dtype,
                            raw_text=text,
                            normalized_value=norm_val,
                            confidence=segment.get("confidence", 0.50),
                            bbox=segment.get("bbox", [0, 0, 100, 30]),
                            image_id=image_id,
                            panel="front",
                            status=DeclarationStatus.EXTRACTED
                        ))
                        found_types.add(dtype)
                        break

    # Second pass: Concatenate consecutive OCR blocks and try matching
    # (helps when fields span multiple OCR lines)
    if len(ocr_results) >= 2:
        for i in range(len(ocr_results) - 1):
            t1 = ocr_results[i].get("text", "").strip()
            t2 = ocr_results[i + 1].get("text", "").strip()
            if not t1 or not t2:
                continue

            combined = f"{t1} {t2}"
            avg_conf = (ocr_results[i].get("confidence", 0.5) + ocr_results[i+1].get("confidence", 0.5)) / 2

            # Merge bounding boxes
            b1 = ocr_results[i].get("bbox", [0, 0, 100, 30])
            b2 = ocr_results[i+1].get("bbox", [0, 0, 100, 30])
            merged_bbox = [
                min(b1[0], b2[0]), min(b1[1], b2[1]),
                max(b1[2], b2[2]), max(b1[3], b2[3])
            ]

            for dtype, pattern_list in PATTERNS.items():
                if dtype in found_types:
                    continue

                for pattern in pattern_list:
                    try:
                        match = re.search(pattern, combined)
                    except re.error:
                        continue

                    if match:
                        norm_val = clean_extracted_value(dtype, combined, match)
                        if norm_val and len(norm_val) >= 2:
                            declarations.append(Declaration(
                                type=dtype,
                                raw_text=combined,
                                normalized_value=norm_val,
                                confidence=round(avg_conf, 2),
                                bbox=merged_bbox,
                                image_id=image_id,
                                panel="front",
                                status=DeclarationStatus.EXTRACTED
                            ))
                            found_types.add(dtype)
                            break

    return declarations
