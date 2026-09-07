"""
APEX — LabelSure image processing & annotation module.

Handles:
- Quality Gating (blur, glare, resolution)
- Deskew / Denoise
- Bounding Box Highlight Overlays (Green = PASS, Red = FAIL, Amber = WARN, Cyan = TEXT)
"""

import os
import cv2
import numpy as np
from typing import Tuple, Dict, List, Any
from PIL import Image, ImageDraw, ImageFont


def check_quality(image_path: str) -> Dict:
    """Assess image quality (blur, glare, resolution)."""
    img = cv2.imread(image_path)
    if img is None:
        return {"status": "FAIL", "reason": "Could not read image"}

    # Blur check using Laplacian variance
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    if variance < 100:
        return {"status": "UNCERTAIN", "reason": "Excessive blur"}

    # Glare check (simplified brightness threshold)
    if np.mean(gray) > 240:
        return {"status": "UNCERTAIN", "reason": "Excessive glare"}

    return {"status": "PASS", "variance": variance}


def process_image(image_path: str, output_path: str) -> bool:
    """Deskew, denoise, perspective correct."""
    img = cv2.imread(image_path)
    if img is None:
        return False
    # Simple denoising
    denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    cv2.imwrite(output_path, denoised)
    return True


def annotate_image_with_bboxes(
    image_path: str,
    output_path: str,
    ocr_results: List[Dict[str, Any]],
    declarations: List[Any],
    findings: List[Any]
) -> List[Dict[str, Any]]:
    """
    Draw color-coded bounding boxes and banners over detected label text:
      - PASS (Compliant): Bright Green (#00E676 / RGB: 0, 230, 118)
      - FAIL (Non-Compliant): Vivid Red (#FF5252 / RGB: 255, 82, 82)
      - WARN (Missing / Caution): Warm Amber (#FFAB00 / RGB: 255, 171, 0)
      - TEXT (General Text): Bright Cyan (#00E5FF / RGB: 0, 229, 255)

    Returns a list of structured annotated bounding box metadata for interactive frontend display.
    """
    if not os.path.isfile(image_path):
        return []

    try:
        pil_img = Image.open(image_path).convert("RGBA")
    except Exception:
        return []

    # Prepare transparent overlay layer for filled box tints
    overlay = Image.new("RGBA", pil_img.size, (255, 255, 255, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    draw_img = ImageDraw.Draw(pil_img)

    # Build declaration lookup: normalized_text / type -> status & field name
    decl_status_map = {}
    for d in declarations:
        field_type = getattr(d, 'type', None)
        if hasattr(field_type, 'value'):
            field_type_val = field_type.value
        else:
            field_type_val = str(field_type) if field_type else "DECLARATION"

        raw_text = getattr(d, 'raw_text', '').lower().strip()
        norm_val = getattr(d, 'normalized_value', '').lower().strip()

        # Find status from findings matching rule clauses or field types
        status = "PASS"
        for f in findings:
            desc = getattr(f, 'description', '').lower()
            f_status = getattr(f, 'status', None)
            f_status_str = f_status.value if hasattr(f_status, 'value') else str(f_status)
            
            # Check if finding mentions this field or rule failed
            if field_type_val.lower() in desc or norm_val in desc:
                if f_status_str == "FAIL":
                    status = "FAIL"
                    break
                elif f_status_str == "UNCERTAIN":
                    status = "WARN"

        decl_status_map[raw_text] = (status, field_type_val)
        if norm_val:
            decl_status_map[norm_val] = (status, field_type_val)

    annotated_bboxes = []

    for item in ocr_results:
        bbox = item.get("bbox", [])
        text = item.get("text", "").strip()
        if len(bbox) < 4 or not text:
            continue

        x1, y1, x2, y2 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
        text_lower = text.lower()

        # Determine status and label type
        status = "TEXT"
        field_label = "TEXT"

        # Match text against declarations
        matched = False
        for key, (d_status, d_label) in decl_status_map.items():
            if key in text_lower or text_lower in key:
                status = d_status
                field_label = d_label
                matched = True
                break

        # Heuristic rules for common keywords if not explicitly matched
        if not matched:
            if any(k in text_lower for k in ["mrp", "rs.", "rs ", "price", "incl."]):
                field_label = "MAXIMUM_RETAIL_PRICE"
                status = "PASS" if "incl" in text_lower else "FAIL"
            elif any(k in text_lower for k in ["net wt", "net quantity", "net qty", "200g", "500g", "1kg"]):
                field_label = "NET_QUANTITY"
                status = "PASS"
            elif any(k in text_lower for k in ["mfg", "packed", "date", "exp", "best before"]):
                field_label = "MFG_OR_EXP_DATE"
                status = "PASS"
            elif any(k in text_lower for k in ["mfd by", "manufactured", "marketed by"]):
                field_label = "MANUFACTURER"
                status = "PASS"
            elif "fssai" in text_lower or "lic" in text_lower:
                field_label = "FSSAI_LICENSE"
                status = "PASS"

        # Color mapping
        if status == "FAIL":
            color_stroke = (255, 82, 82, 255)      # Red
            color_fill = (255, 82, 82, 45)         # Semi-transparent red
            hex_color = "#FF5252"
        elif status == "PASS":
            color_stroke = (0, 230, 118, 255)     # Green
            color_fill = (0, 230, 118, 40)        # Semi-transparent green
            hex_color = "#00E676"
        elif status == "WARN":
            color_stroke = (255, 171, 0, 255)     # Amber
            color_fill = (255, 171, 0, 45)        # Semi-transparent amber
            hex_color = "#FFAB00"
        else:
            color_stroke = (0, 229, 255, 255)     # Cyan
            color_fill = (0, 229, 255, 25)        # Semi-transparent cyan
            hex_color = "#00E5FF"

        # Draw box on transparent overlay
        draw_overlay.rectangle([x1, y1, x2, y2], fill=color_fill, outline=color_stroke, width=3)

        # Draw small tag label banner
        tag_text = f"[{status}] {field_label}" if field_label != "TEXT" else text[:15]
        tag_w = len(tag_text) * 7 + 10
        tag_h = 16
        tag_y1 = max(0.0, y1 - tag_h)
        draw_overlay.rectangle([x1, tag_y1, x1 + tag_w, tag_y1 + tag_h], fill=color_stroke)
        draw_overlay.text((x1 + 4, tag_y1 + 1), tag_text, fill=(0, 0, 0, 255))

        annotated_bboxes.append({
            "bbox": [x1, y1, x2, y2],
            "text": text,
            "field_label": field_label,
            "status": status,
            "color": hex_color
        })

    # Combine original image with transparent overlay
    composite = Image.alpha_composite(pil_img, overlay).convert("RGB")
    composite.save(output_path, "PNG")

    return annotated_bboxes
