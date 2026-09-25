"""OCR engine loading + inference. Ported from pipeline/main.py.

EasyOCR is preferred; PaddleOCR is a fallback if EasyOCR isn't installed.
This is the one place that decides which engine is available — pipeline/main.py
and any future job worker both import OCR_ENGINE from here instead of each
running their own try/except import.
"""

import logging
import sys
from typing import List, Tuple

import cv2
import numpy as np

logger = logging.getLogger("ANPR_Engine")

try:
    import easyocr as _easyocr
    OCR_ENGINE = "easyocr"
except ImportError:
    try:
        from paddleocr import PaddleOCR as _PaddleOCR
        OCR_ENGINE = "paddle"
    except ImportError:
        logger.error("No OCR engine found. Install with: pip install easyocr  OR  pip install paddleocr paddlepaddle")
        sys.exit(1)

ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def load_ocr_engine(device: str):
    if OCR_ENGINE == "easyocr":
        logger.info("Initializing EasyOCR engine...")
        return _easyocr.Reader(["en"], gpu=(device != "cpu"))
    logger.info("Initializing PaddleOCR engine (fallback)...")
    for kwargs in [{"use_textline_orientation": True, "lang": "en"}, {"lang": "en"}]:
        try:
            return _PaddleOCR(**kwargs)
        except Exception:
            pass
    return _PaddleOCR(lang="en")


def _preprocess_variants(plate_img: np.ndarray) -> List[np.ndarray]:
    """Pad + upscale, then return color / CLAHE / Otsu / inverted-Otsu variants."""
    h = plate_img.shape[0]
    pad = max(8, int(h * 0.3))
    img = cv2.copyMakeBorder(plate_img, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
    scale = max(1.0, 128.0 / img.shape[0])
    img = cv2.resize(img, (int(img.shape[1] * scale), int(img.shape[0] * scale)), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe_gray = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)
    _, otsu = cv2.threshold(cv2.bilateralFilter(gray, 9, 75, 75), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return [
        img,
        cv2.cvtColor(clahe_gray, cv2.COLOR_GRAY2BGR),
        cv2.cvtColor(otsu, cv2.COLOR_GRAY2BGR),
        cv2.cvtColor(cv2.bitwise_not(otsu), cv2.COLOR_GRAY2BGR),
    ]


def run_ocr_inference(engine, plate_img: np.ndarray) -> List[Tuple[str, float]]:
    """Run OCR across preprocessing variants. Returns (text, confidence) pairs."""
    if plate_img is None or plate_img.size == 0:
        return []

    results: List[Tuple[str, float]] = []
    for variant in _preprocess_variants(plate_img):
        try:
            if OCR_ENGINE == "easyocr":
                detections = engine.readtext(variant, allowlist=ALLOWLIST, detail=1)
                if detections:
                    detections.sort(key=lambda d: min(pt[1] for pt in d[0]))  # top-to-bottom rows
                    combined_text = "".join(text for _, text, _ in detections)
                    avg_conf = sum(conf for _, _, conf in detections) / len(detections)
                    results.append((combined_text, float(avg_conf)))
            else:
                for det in (False, True):
                    out = engine.ocr(variant, det=det, rec=True)
                    items = (out[0] if out and isinstance(out[0], list) else out) or []
                    for item in items:
                        try:
                            raw, conf = (item[1][0], item[1][1]) if det else (item[0], item[1])
                            results.append((str(raw), float(conf)))
                        except Exception:
                            pass
        except Exception as e:
            logger.debug(f"OCR variant error: {e}")

    return results
