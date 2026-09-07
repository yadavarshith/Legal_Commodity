"""
APEX — Context-Aware Legal Metrology Declaration Extractor.
Maps OCR text regions to strict Declaration contracts for all Legal Metrology statutory fields.
Designed to handle real OCR text, multi-line packaging layouts, noise, and OCR typos.
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
        r"(?i)(?:Brand|Product\s*Name|Commodity\s*Name|Name\s*of\s*(?:the\s*)?(?:Product|Commodity|Item))[\s:]+(.+)",
        r"(?i)(?:Product|Commodity|Item)\s*:\s*(.+)",
        r"(?i)\b(?:Organic|Basmati|Rice|Atta|Flour|Wheat|Oil|Refined|Ghee|Milk|Butter|Paneer|Spices|Masala|Tea|Coffee|Sugar|Salt|Dal|Pulses|Juice|Water|Soda|Biscuits|Cookies|Noodles|Snacks|Chips|Soap|Lotion|Cream|Shampoo|Face\s*Wash|Detergent)\b.+",
    ],
    DeclarationType.MANUFACTURER: [
        r"(?i)(?:Mfg\.?\s*(?:&|and)?\s*(?:Mkd|Mktd|Packed|Pkd)\.?\s*(?:By)?|Manufactured\s*(?:By|&\s*Packed\s*By)|Mfg\.?\s*By|Packed\s*By|Packer|Importer|Marketed\s*By|Distributed\s*By)[\s:]+(.+)",
        r"(?i)(?:Manufacturer|Packer\s*Address|Regd\.?\s*(?:Office|Off))[\s:]+(.+)",
        r"(?i).+(?:Pvt\.?\s*Ltd\.?|Limited|Co(?:\.|operative)?|Inc\.?|Corp(?:oration)?|Industries|Refineries|Labs|Holdings|Foods|Herbals|Organics)\b.+",
    ],
    DeclarationType.NET_QUANTITY: [
        r"(?i)(?:Net\s*(?:Qty|Wt|Weight|Quantity|Vol|Volume|Content))[\s:.]*(\d+(?:[.,]\d+)?\s*(?:g|gm|gms|kg|kgs|ml|mL|l|ltr|litres?|liters?|pcs|pieces|units?))\b",
        r"(?i)(?:Contents?|Quantity|Wt\.?)[\s:.]*(\d+(?:[.,]\d+)?\s*(?:g|gm|gms|kg|kgs|ml|mL|l|ltr))\b",
        r"\b(\d+(?:[.,]\d+)?\s*(?:g|gm|gms|kg|kgs|ml|mL|l|ltr))\b",
    ],
    DeclarationType.MRP: [
        r"(?i)(?:M\.?\s*R\.?\s*P\.?|Maximum\s*Retail\s*Price|Max\.?\s*Price)[\s:.]*(?:Rs\.?|INR|₹)?\s*(\d+(?:[.,]\d{1,2})?.*)",
        r"(?i)(?:Rs\.?|INR|₹)\s*(\d+(?:[.,]\d{1,2})?)\s*(?:\(?\s*(?:Incl|incl).*)?",
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
        r"\b\+?91[\s\-]?\d{10}\b",
    ],
    DeclarationType.COUNTRY_OF_ORIGIN: [
        r"(?i)(?:Country\s*of\s*Origin|Origin|Made\s*[Ii]n|Product\s*of|Imported\s*[Ff]rom)[\s:.]*(.+)",
        r"(?i)\b(India|China|USA|United\s*States|UK|Germany|Switzerland|France|Japan|South\s*Korea|Thailand|Vietnam|Indonesia|Malaysia|Bangladesh|Sri\s*Lanka|Italy|Spain|Australia|Canada|Brazil|Mexico|Turkey|Taiwan|Netherlands|Belgium|Singapore|Nepal)\b",
    ],
}


def clean_extracted_value(dtype: DeclarationType, raw_text: str, match: re.Match) -> str:
    """Extract clean, normalized value from regex match without prefix clutter."""
    if match.groups():
        val = match.group(1).strip()
    else:
        val = match.group(0).strip()

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

    val = re.sub(r"[\s|]+$", "", val).strip()
    val = val.strip(".:;,- ")

    return val if val and len(val) >= 2 else ""


def extract_declarations(ocr_results: List[Dict], image_id: str) -> List[Declaration]:
    """
    Map OCR text segments to Declaration models.
    Iterates all OCR blocks and matches against Legal Metrology patterns.
    Also concatenates 2-line and 3-line adjacent blocks for multi-line packaging layouts.
    Includes dynamic fallback for PRODUCT_NAME extraction from top prominent OCR lines.
    """
    declarations = []
    found_types = set()

    if not ocr_results:
        return declarations

    # 1st Pass: Match individual OCR blocks
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

    # 2nd Pass: Concatenate 2 and 3 consecutive OCR blocks
    n = len(ocr_results)
    if n >= 2:
        for k in range(2, 4):
            if n < k:
                continue
            for i in range(n - k + 1):
                group = ocr_results[i : i + k]
                texts = [g.get("text", "").strip() for g in group if g.get("text", "").strip()]
                if not texts:
                    continue

                combined = " ".join(texts)
                avg_conf = sum(g.get("confidence", 0.5) for g in group) / len(group)

                merged_bbox = [
                    min(g.get("bbox", [0, 0, 100, 30])[0] for g in group),
                    min(g.get("bbox", [0, 0, 100, 30])[1] for g in group),
                    max(g.get("bbox", [0, 0, 100, 30])[2] for g in group),
                    max(g.get("bbox", [0, 0, 100, 30])[3] for g in group),
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

    # 3rd Pass: Dynamic Fallback for PRODUCT_NAME if not explicitly matched
    if DeclarationType.PRODUCT_NAME not in found_types:
        boilerplate_keywords = [
            "mfg", "manufactured", "packed", "packer", "mrp", "rs", "inr", "net wt", "net qty",
            "net weight", "net quantity", "ingredients", "batch", "exp", "expiry", "best before",
            "customer care", "helpline", "email", "address", "phone", "lic no", "fssai", "registered",
            "marketed", "imported"
        ]
        
        best_candidate = None
        for segment in ocr_results:
            text = segment.get("text", "").strip()
            if not text or len(text) < 3 or len(text) > 80:
                continue

            lower_text = text.lower()
            # Skip boilerplate lines
            if any(bp in lower_text for bp in boilerplate_keywords):
                continue
            # Must contain letters
            if not re.search(r"[a-zA-Z]{2,}", text):
                continue

            best_candidate = segment
            break

        if best_candidate:
            norm_val = best_candidate.get("text", "").strip()
            declarations.append(Declaration(
                type=DeclarationType.PRODUCT_NAME,
                raw_text=norm_val,
                normalized_value=norm_val,
                confidence=best_candidate.get("confidence", 0.75),
                bbox=best_candidate.get("bbox", [0, 0, 100, 30]),
                image_id=image_id,
                panel="front",
                status=DeclarationStatus.EXTRACTED
            ))

    return declarations
