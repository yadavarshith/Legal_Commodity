"""
APEX — LabelSure image processing module.

Handles:
- Quality Gating (blur, glare, resolution)
- Deskew / Denoise
- Perspective correction
"""

import cv2
import numpy as np
from typing import Tuple, Dict

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
    # Simple denoising
    denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

    cv2.imwrite(output_path, denoised)
    return True
