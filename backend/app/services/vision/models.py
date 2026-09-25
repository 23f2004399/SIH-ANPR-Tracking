"""Model loading for vehicle + plate detection. Ported from pipeline/main.py
so the FastAPI job workers (Phase 2) and the CLI tool share one copy."""

import logging
import os
import urllib.request

import torch
from ultralytics import YOLO

logger = logging.getLogger("ANPR_Engine")

PLATE_MODEL_DOWNLOAD_URL = "https://huggingface.co/Koushim/yolov8-license-plate-detection/resolve/main/best.pt"


def select_device(explicit: str = "") -> str:
    if explicit:
        return explicit.lower()
    if torch.cuda.is_available():
        logger.info(f"Detected GPU: {torch.cuda.get_device_name(0)}")
        return "cuda"
    logger.warning("No CUDA GPU detected. Running on CPU.")
    return "cpu"


def load_vehicle_model(model_name_or_path: str, device: str) -> YOLO:
    logger.info(f"Loading Vehicle Detection Model: {model_name_or_path}...")
    try:
        model = YOLO(model_name_or_path)
        model.to(device)
        return model
    except Exception as e:
        logger.warning(f"Could not load '{model_name_or_path}' ({e}). Falling back to 'yolov8n.pt'...")
        model = YOLO("yolov8n.pt")
        model.to(device)
        return model


def load_plate_model(model_path: str, device: str, vehicle_model_fallback: str) -> YOLO:
    """Load the plate detector, auto-downloading and caching weights if needed."""
    if not os.path.exists(model_path):
        local_weights_name = "yolov8n_plate.pt"
        if os.path.exists(local_weights_name):
            model_path = local_weights_name
        else:
            logger.info("Plate detector not found locally. Downloading pre-trained weights from Hugging Face...")
            try:
                req = urllib.request.Request(PLATE_MODEL_DOWNLOAD_URL, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req) as resp, open(local_weights_name, "wb") as f_out:
                    f_out.write(resp.read())
                logger.info(f"Saved plate detector weights to: {local_weights_name}")
                model_path = local_weights_name
            except Exception as e:
                logger.error(f"Failed to auto-download plate weights: {e}")
                logger.warning("Falling back to vehicle detector for plate model.")
                model_path = vehicle_model_fallback

    logger.info(f"Loading Plate Detector: {model_path}...")
    model = YOLO(model_path)
    model.to(device)
    return model
