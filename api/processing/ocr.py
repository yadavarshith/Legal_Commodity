"""
OCR module using PaddleOCR.
"""

from paddleocr import PaddleOCR
import numpy as np

# Initialize OCR locally
ocr = PaddleOCR(use_angle_cls=True, lang='en')

def extract_text(image_path: str):
    """
    Run OCR and return list of (bbox, text, confidence).
    """
    result = ocr.ocr(image_path, cls=True)
    if not result or result[0] is None:
        return []

    # Flatten result
    processed = []
    for line in result[0]:
        bbox = line[0] # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        text = line[1][0]
        confidence = line[1][1]
        processed.append({
            "bbox": [float(bbox[0][0]), float(bbox[0][1]), float(bbox[2][0]), float(bbox[2][1])],
            "text": text,
            "confidence": float(confidence)
        })
    return processed
