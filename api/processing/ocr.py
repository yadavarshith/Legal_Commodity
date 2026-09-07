"""
APEX — LabelSure Real OCR Engine.
Extracts text from package label images using:
  1. PyTesseract (primary — Tesseract v5.4 installed)
  2. RapidOCR (fallback — ONNX-based, no external binary)
No hardcoded/static product data. Every image is genuinely read.
"""

import os
import logging
from typing import List, Dict, Any
from PIL import Image, ImageFilter, ImageEnhance

logger = logging.getLogger("labelsure.ocr")

import shutil

# Dynamic Tesseract lookup
TESSERACT_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
]

def _find_tesseract_binary() -> str:
    path = shutil.which("tesseract")
    if path:
        return path
    for candidate in TESSERACT_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    return ""

# Lazy-loaded RapidOCR engine
_rapidocr_engine = None


def _preprocess_image(img: Image.Image) -> Image.Image:
    """Enhance image for better OCR accuracy on package labels."""
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Resize if too small (OCR works better on larger images)
    w, h = img.size
    if max(w, h) < 800:
        scale = 800 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Sharpen for clearer text edges
    img = img.filter(ImageFilter.SHARPEN)

    # Enhance contrast for text visibility
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)

    return img


def _ocr_with_pytesseract(image_path: str) -> List[Dict[str, Any]]:
    """Run PyTesseract OCR on the image using installed Tesseract binary."""
    tess_bin = _find_tesseract_binary()
    if not tess_bin:
        return []

    try:
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = tess_bin
        
        img = Image.open(image_path)
        img = _preprocess_image(img)

        # Use detailed data extraction with line grouping
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT,
                                          config='--oem 3 --psm 6')
        
        # Group words into lines by block_num + line_num
        lines: Dict[tuple, dict] = {}
        n_boxes = len(data['text'])

        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = float(data['conf'][i])
            if not text or conf < 20:
                continue

            line_key = (data['block_num'][i], data['line_num'][i])
            if line_key not in lines:
                lines[line_key] = {
                    "words": [],
                    "x1": float(data['left'][i]),
                    "y1": float(data['top'][i]),
                    "x2": float(data['left'][i] + data['width'][i]),
                    "y2": float(data['top'][i] + data['height'][i]),
                    "confs": []
                }

            line = lines[line_key]
            line["words"].append(text)
            line["x1"] = min(line["x1"], float(data['left'][i]))
            line["y1"] = min(line["y1"], float(data['top'][i]))
            line["x2"] = max(line["x2"], float(data['left'][i] + data['width'][i]))
            line["y2"] = max(line["y2"], float(data['top'][i] + data['height'][i]))
            line["confs"].append(conf)

        results = []
        for line_key, line in sorted(lines.items()):
            full_text = " ".join(line["words"])
            if len(full_text) < 2:
                continue
            avg_conf = sum(line["confs"]) / len(line["confs"]) if line["confs"] else 50.0
            results.append({
                "bbox": [round(line["x1"], 1), round(line["y1"], 1),
                         round(line["x2"], 1), round(line["y2"], 1)],
                "text": full_text,
                "confidence": round(min(avg_conf / 100.0, 1.0), 2)
            })

        if results:
            logger.info("PyTesseract extracted %d text lines from %s", len(results), os.path.basename(image_path))
        return results

    except Exception as exc:
        logger.warning("PyTesseract OCR failed for %s: %s", image_path, exc)
        return []


def _get_rapidocr_engine():
    """Lazily initialize RapidOCR engine."""
    global _rapidocr_engine
    if _rapidocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _rapidocr_engine = RapidOCR()
            logger.info("RapidOCR engine initialized successfully.")
        except ImportError:
            logger.warning("rapidocr-onnxruntime not installed.")
            _rapidocr_engine = False
        except Exception as exc:
            logger.warning("RapidOCR init failed: %s", exc)
            _rapidocr_engine = False
    return _rapidocr_engine if _rapidocr_engine is not False else None


def _ocr_with_rapidocr(image_path: str) -> List[Dict[str, Any]]:
    """Fallback: Run RapidOCR (ONNX-based) on the image."""
    engine = _get_rapidocr_engine()
    if engine is None:
        return []

    try:
        result, _ = engine(image_path)
        if not result:
            return []

        results = []
        for item in result:
            bbox_points = item[0]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
            text = item[1]
            confidence = float(item[2]) if len(item) > 2 else 0.80

            if not text or not text.strip():
                continue

            xs = [p[0] for p in bbox_points]
            ys = [p[1] for p in bbox_points]
            x1, y1 = min(xs), min(ys)
            x2, y2 = max(xs), max(ys)

            results.append({
                "bbox": [round(float(x1), 1), round(float(y1), 1),
                         round(float(x2), 1), round(float(y2), 1)],
                "text": text.strip(),
                "confidence": round(confidence, 2)
            })

        if results:
            logger.info("RapidOCR extracted %d text blocks from %s", len(results), os.path.basename(image_path))
        return results

    except Exception as exc:
        logger.warning("RapidOCR failed for %s: %s", image_path, exc)
        return []


def extract_text(image_path: str) -> List[Dict[str, Any]]:
    """
    Run OCR on image_path and return list of:
    [{ "bbox": [x1, y1, x2, y2], "text": "...", "confidence": float }]

    Tries PyTesseract first (Tesseract v5.4 binary), then RapidOCR fallback.
    Returns empty list if all engines fail — never returns fake data.
    """
    if not os.path.isfile(image_path):
        logger.error("Image file not found: %s", image_path)
        return []

    # Try PyTesseract with installed Tesseract binary
    results = _ocr_with_pytesseract(image_path)
    if results:
        return results

    # Fallback: RapidOCR (ONNX-based, no external binary)
    results = _ocr_with_rapidocr(image_path)
    if results:
        return results

    # If all engines fail, return empty — no fake data
    logger.warning("All OCR engines failed for %s. No text extracted.", image_path)
    return []
