#!/usr/bin/env python3
"""
City-Wide Multi-Camera ANPR Trajectory Tracking and Vehicle Analytics Pipeline
================================================================================
SIH Problem Statement: 26127 (Bharat Electronics Limited)
Hardware Target: NVIDIA GPU (GTX 1650 4GB / RTX series)

Key Features:
- YOLO11 (yolo11n.pt) Vehicle Detection + ByteTrack Multi-Camera Tracking
- High-Precision License Plate Localization with cached weights (yolov8n_plate.pt)
- Multi-Pass PaddleOCR (DBNet Text Detection + Fallback Direct Recognition)
- High-Accuracy Crop Filter: Only saves vehicle & plate crops with confident plate reads (>= min_save_conf)
- Detailed step-by-step PaddleOCR diagnostic logs in terminal
- Dynamic 3-stage bounding box tags: DETECTING... -> RECOGNIZING... -> [PLATE NUMBER]
- Unique video output naming based on input video stems
"""

import os
import sys
import time
import csv
import re
import argparse
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any

import cv2
import numpy as np
import torch
from ultralytics import YOLO

# Indian plate grammar + glyph-confusion repair, shared with the ocr.py evaluator
# so the pipeline and the diagnostic tool can never drift apart.
from ocr import correct_indian_plate, STATE_CODES

# Suppress internal noise while keeping detailed ANPR engine logs
os.environ["PPOCR_LOG_LEVEL"] = "ERROR"
os.environ["FLAGS_allocator_strategy"] = "auto_growth"

# Configure logging for crystal-clear terminal output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ANPR_Engine")

# OCR Engine: EasyOCR (primary) with PaddleOCR fallback
try:
    import easyocr as _easyocr
    _OCR_ENGINE = "easyocr"
except ImportError:
    try:
        from paddleocr import PaddleOCR as _PaddleOCR
        _OCR_ENGINE = "paddle"
    except ImportError:
        logger.error("No OCR engine found. Install with: pip install easyocr  OR  pip install paddleocr paddlepaddle")
        sys.exit(1)


# ==============================================================================
# Helper Utilities: Text Normalization & Confidence-Weighted Voting
# ==============================================================================

def clean_plate_text(raw_text: str) -> str:
    """
    Standardize license plate strings: removes noise, non-alphanumeric chars,
    and converts to uppercase.
    """
    if not raw_text:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", str(raw_text)).upper()
    return cleaned


# State codes this deployment actually sees. Breaks ties when repairing a
# garbled state field (TK is one substitution from both TR and TN).
STATE_PRIOR: Tuple[str, ...] = ()

# Wall-clock format used on the video overlay (as an operator would read it)
# and in the CSV (ISO-like, so timestamps sort lexicographically for the
# cross-camera trajectory search).
OVERLAY_TS_FMT = "%d/%m/%Y %H:%M:%S"
CSV_TS_FMT = "%Y-%m-%d %H:%M:%S.%f"

_RECORDED_AT_FORMATS = [
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M",
    "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M",
]


def parse_recorded_at(value: str) -> datetime:
    """Parse the wall-clock time at which the source footage started recording."""
    value = value.strip()
    for fmt in _RECORDED_AT_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Unrecognised --recorded_at '{value}'. "
        f"Try '2026-08-31 15:58:00' or '31/08/2026 15:58'."
    )


def resolve_best_plate(ocr_reads: List[Tuple[str, float]]) -> Tuple[str, float]:
    """
    Resolve one plate from every OCR read collected across a tracklet.

    Votes per character position rather than on whole strings. Whole-string
    voting splits the vote between reads that differ by a single misread
    character ('IN22DM8143' vs 'TN22DM8143' each score 1); positional voting
    lets them reinforce each other and elect the correct character in each slot.
    The winner is then snapped onto the Indian plate grammar.
    """
    if not ocr_reads:
        return "UNKNOWN", 0.0

    valid_reads = [(t, c) for t, c in ocr_reads if 4 <= len(t) <= 12] or list(ocr_reads)

    def vote_at_length(target_len: int) -> Tuple[str, float, float]:
        """Per-position winner among reads of exactly this length."""
        same_len = [(t, c) for t, c in valid_reads if len(t) == target_len]
        chars, agreement = [], 0.0
        for i in range(target_len):
            column: Dict[str, float] = defaultdict(float)
            for text, conf in same_len:
                column[text[i]] += conf
            winner = max(column, key=lambda k: column[k])
            chars.append(winner)
            agreement += column[winner] / sum(column.values())
        mean_conf = sum(c for _, c in same_len) / len(same_len)
        return "".join(chars), agreement / target_len, mean_conf

    # Agree on a length first, otherwise positions don't line up. Weight the
    # length vote by confidence * length: a partial read of a plate is both
    # common and very confident ('3071' at 94%), so scoring on confidence alone
    # lets a fragment beat the full plate. Length is the tie-breaker that
    # matches the actual failure mode.
    len_scores: Dict[int, float] = defaultdict(float)
    for text, conf in valid_reads:
        len_scores[len(text)] += conf * len(text)
    ranked = sorted(len_scores, key=lambda k: len_scores[k], reverse=True)

    # Prefer the highest-ranked length that actually yields a well-formed plate.
    fallback = None
    for target_len in ranked:
        voted, agreement, mean_conf = vote_at_length(target_len)
        corrected, is_valid = correct_indian_plate(voted, STATE_PRIOR)
        result = (corrected, round(agreement * mean_conf * 100.0, 2))
        if is_valid:
            return result
        if fallback is None:
            fallback = result

    return fallback if fallback else ("UNKNOWN", 0.0)


# ==============================================================================
# Multi-Camera ANPR Pipeline Engine
# ==============================================================================

class MultiCameraANPRPipeline:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.device = self._select_device()
        logger.info(f"Compute Device: {self.device.upper()}")

        # All feeds share one recording start instant (see _wallclock).
        self.recorded_at = args.recorded_at
        logger.info(f"Footage recording start (all cameras): "
                    f"{self.recorded_at.strftime(OVERLAY_TS_FMT)}")

        # Ensure output directories exist
        os.makedirs(self.args.output_dir, exist_ok=True)
        self.vehicle_crops_dir = os.path.join(self.args.output_dir, "crops", "vehicles")
        self.plate_crops_dir = os.path.join(self.args.output_dir, "crops", "plates")
        os.makedirs(self.vehicle_crops_dir, exist_ok=True)
        os.makedirs(self.plate_crops_dir, exist_ok=True)

        self.csv_log_path = os.path.join(self.args.output_dir, "vehicle_logs.csv")
        self._init_csv_log()

        # Load models
        self.vehicle_model = self._load_vehicle_model(self.args.vehicle_model)
        self.plate_model = self._load_plate_model(self.args.plate_model)
        self.ocr_engine = self._load_ocr_engine()

        # Filter for vehicle categories (COCO indices: 2: car, 3: motorcycle, 5: bus, 7: truck)
        self.vehicle_classes = [2, 3, 5, 7]

    def _select_device(self) -> str:
        """Auto-detect CUDA GPU or CPU."""
        if self.args.device:
            return self.args.device.lower()
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"Detected GPU: {gpu_name}")
            return "cuda"
        logger.warning("No CUDA GPU detected. Running on CPU.")
        return "cpu"

    def _load_vehicle_model(self, model_name_or_path: str) -> YOLO:
        """
        Load vehicle detector: Defaults to latest YOLO11 (yolo11n.pt) with fallback to yolov8n.pt.
        """
        logger.info(f"Loading Vehicle Detection Model: {model_name_or_path}...")
        try:
            model = YOLO(model_name_or_path)
            model.to(self.device)
            return model
        except Exception as e:
            logger.warning(f"Could not load '{model_name_or_path}' ({e}). Falling back to 'yolov8n.pt'...")
            model = YOLO("yolov8n.pt")
            model.to(self.device)
            return model

    def _load_plate_model(self, model_path: str) -> YOLO:
        """
        Load specialized License Plate detector. Auto-downloads and caches weights locally if needed.
        """
        if not os.path.exists(model_path):
            local_weights_name = "yolov8n_plate.pt"
            if os.path.exists(local_weights_name):
                model_path = local_weights_name
            else:
                logger.info("Plate detector not found locally. Downloading pre-trained weights from Hugging Face...")
                download_url = "https://huggingface.co/Koushim/yolov8-license-plate-detection/resolve/main/best.pt"
                try:
                    import urllib.request
                    req = urllib.request.Request(download_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req) as resp, open(local_weights_name, "wb") as f_out:
                        f_out.write(resp.read())
                    logger.info(f"Saved plate detector weights to: {local_weights_name}")
                    model_path = local_weights_name
                except Exception as e:
                    logger.error(f"Failed to auto-download plate weights: {e}")
                    logger.warning("Falling back to vehicle detector for plate model.")
                    model_path = self.args.vehicle_model

        logger.info(f"Loading Plate Detector: {model_path}...")
        model = YOLO(model_path)
        model.to(self.device)
        return model

    def _load_ocr_engine(self):
        """Load EasyOCR (preferred) or PaddleOCR as fallback."""
        if _OCR_ENGINE == "easyocr":
            logger.info("Initializing EasyOCR engine...")
            return _easyocr.Reader(["en"], gpu=(self.device != "cpu"))
        else:
            logger.info("Initializing PaddleOCR engine (fallback)...")
            for kwargs in [{"use_textline_orientation": True, "lang": "en"}, {"lang": "en"}]:
                try: return _PaddleOCR(**kwargs)
                except Exception: pass
            return _PaddleOCR(lang="en")

    def _run_ocr_inference(self, plate_img: np.ndarray, track_id: int, camera_id: str, frame_idx: int) -> List[Tuple[str, float]]:
        """Run OCR on a license plate crop. Returns list of (text, confidence) tuples."""
        if plate_img is None or plate_img.size == 0:
            return []

        h, w = plate_img.shape[:2]
        logger.info(f"[{camera_id} | Frame {frame_idx:04d}] 🔍 Track #{track_id}: Running OCR on {w}x{h} plate crop...")

        # Preprocessing: pad + upscale to >= 128px height for legibility
        pad = max(8, int(h * 0.3))
        img = cv2.copyMakeBorder(plate_img, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
        scale = max(1.0, 128.0 / img.shape[0])
        img = cv2.resize(img, (int(img.shape[1]*scale), int(img.shape[0]*scale)), interpolation=cv2.INTER_CUBIC)

        # Build variants: color, CLAHE-sharpened, Otsu binary
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe_gray = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
        _, otsu = cv2.threshold(cv2.bilateralFilter(gray, 9, 75, 75), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants = [img, cv2.cvtColor(clahe_gray, cv2.COLOR_GRAY2BGR),
                    cv2.cvtColor(otsu, cv2.COLOR_GRAY2BGR),
                    cv2.cvtColor(cv2.bitwise_not(otsu), cv2.COLOR_GRAY2BGR)]

        results: List[Tuple[str, float]] = []
        ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

        for v in variants:
            try:
                if _OCR_ENGINE == "easyocr":
                    detections = self.ocr_engine.readtext(v, allowlist=ALLOWLIST, detail=1)
                    if detections:
                        # Sort by top-Y of bounding box so rows are read top-to-bottom
                        detections.sort(key=lambda d: min(pt[1] for pt in d[0]))
                        combined_text = "".join(text for _, text, _ in detections)
                        avg_conf = sum(conf for _, _, conf in detections) / len(detections)
                        results.append((combined_text, float(avg_conf)))
                else:  # paddle fallback
                    for det in [False, True]:
                        out = self.ocr_engine.ocr(v, det=det, rec=True)
                        items = (out[0] if out and isinstance(out[0], list) else out) or []
                        for item in items:
                            try:
                                raw, conf = (item[1][0], item[1][1]) if det else (item[0], item[1])
                                results.append((str(raw), float(conf)))
                            except Exception:
                                pass
            except Exception as e:
                logger.debug(f"OCR variant error track #{track_id}: {e}")

        if results:
            logger.info(f"[{camera_id} | Frame {frame_idx:04d}] 🔤 OCR raw output: {results}")
        else:
            logger.info(f"[{camera_id} | Frame {frame_idx:04d}] ❌ OCR returned no text.")
        return results

    def _wallclock(self, frame_idx: int, fps: float) -> datetime:
        """
        Map a frame index to the real-world time that frame was recorded.

        Every camera is anchored to the same --recorded_at instant, which is what
        makes cross-camera trajectory search work: the three prototype clips were
        started together, so equal wall-clock times mean the same real moment even
        though the feeds are processed sequentially.
        """
        return self.recorded_at + timedelta(seconds=frame_idx / max(fps, 1.0))

    def _init_csv_log(self):
        """Initialize vehicle_logs.csv with headers if not present."""
        if not os.path.exists(self.csv_log_path):
            with open(self.csv_log_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "camera_id",
                    "track_id",
                    "entry_timestamp",          # real wall-clock time, for trajectory search
                    "exit_timestamp",
                    "plate_number",
                    "average_ocr_confidence",
                    "entry_offset_sec",         # seconds into the source clip, for debugging
                    "exit_offset_sec"
                ])
            logger.info(f"Initialized vehicle log file: {self.csv_log_path}")

    def _log_track_to_csv(self, camera_id: str, track_id: int, track_data: dict, fps: float):
        """
        Finalize and append tracklet record to CSV.
        Only save image crops if plate was recognized with decent confidence (>= min_save_conf).
        """
        best_plate, avg_conf = resolve_best_plate(track_data["ocr_reads"])
        
        entry_sec = track_data["entry_frame"] / max(fps, 1.0)
        exit_sec = track_data["last_seen_frame"] / max(fps, 1.0)

        entry_dt = self._wallclock(track_data["entry_frame"], fps)
        exit_dt = self._wallclock(track_data["last_seen_frame"], fps)
        # Millisecond precision: %f gives microseconds, which is false precision here.
        entry_ts = entry_dt.strftime(CSV_TS_FMT)[:-3]
        exit_ts = exit_dt.strftime(CSV_TS_FMT)[:-3]

        with open(self.csv_log_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                camera_id,
                track_id,
                entry_ts,
                exit_ts,
                best_plate,
                f"{avg_conf:.2f}",
                f"{entry_sec:.2f}",
                f"{exit_sec:.2f}"
            ])

        # High-Accuracy Crop Filter: Only save crops if plate is recognized with decent accuracy
        is_confident = (best_plate != "UNKNOWN") and (avg_conf >= self.args.min_save_conf)

        if is_confident:
            # Save single best vehicle crop
            if track_data.get("best_vehicle_crop") is not None:
                v_crop_path = os.path.join(self.vehicle_crops_dir, f"{camera_id}_track_{track_id}.jpg")
                cv2.imwrite(v_crop_path, track_data["best_vehicle_crop"])

            # Save single best plate crop
            if track_data.get("best_plate_crop") is not None:
                p_crop_path = os.path.join(self.plate_crops_dir, f"{camera_id}_track_{track_id}.jpg")
                cv2.imwrite(p_crop_path, track_data["best_plate_crop"])

            logger.info(
                f"[{camera_id}] 🏁 Track #{track_id} EXITED | "
                f"Plate: '{best_plate}' (Avg Conf: {avg_conf:.1f}%) | "
                f"Time: {entry_dt:%H:%M:%S} -> {exit_dt:%H:%M:%S} | 💾 Saved Verified Crops"
            )
        else:
            logger.info(
                f"[{camera_id}] 🏁 Track #{track_id} EXITED | "
                f"Plate: '{best_plate}' (Avg Conf: {avg_conf:.1f}%) | "
                f"Time: {entry_dt:%H:%M:%S} -> {exit_dt:%H:%M:%S} | ⏭️ Skipped crop saving (< {self.args.min_save_conf}% conf)"
            )

    # --------------------------------------------------------------------------
    # Video Stream Processing Routine
    # --------------------------------------------------------------------------
    def process_video_stream(self, video_path: str, camera_id: str):
        """
        Process a video feed sequentially with full-frame tracking & detailed terminal telemetry.
        """
        if not os.path.exists(video_path):
            logger.error(f"[{camera_id}] Video file not found: {video_path}")
            return

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"[{camera_id}] Failed to open video: {video_path}")
            return

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        input_filename = os.path.basename(video_path)
        input_stem = os.path.splitext(input_filename)[0]
        out_video_name = f"annotated_{input_stem}.mp4"
        out_video_path = os.path.join(self.args.output_dir, out_video_name)

        logger.info(f"\n" + "="*70)
        logger.info(f"▶ STARTING FEED: {camera_id} | Input: '{input_filename}'")
        logger.info(f"  Resolution: {frame_width}x{frame_height} @ {fps:.1f} FPS | Total Frames: {total_frames}")
        logger.info(f"  Target Output Video: '{out_video_path}'")
        logger.info("="*70)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = None
        if not self.args.no_video:
            video_writer = cv2.VideoWriter(out_video_path, fourcc, fps, (frame_width, frame_height))

        active_tracks: Dict[int, dict] = {}
        frame_idx = 0
        logged_count = 0
        start_time = time.time()

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break
                if self.args.max_frames and frame_idx >= self.args.max_frames:
                    logger.info(f"[{camera_id}] Reached --max_frames={self.args.max_frames}, stopping early.")
                    break

                frame_idx += 1
                current_frame_plates = []

                # Step 1: Vehicle Detection & Tracking with ByteTrack (No deprecated 'half' argument)
                track_results = self.vehicle_model.track(
                    source=frame,
                    persist=True,
                    tracker="bytetrack.yaml",
                    classes=self.vehicle_classes,
                    conf=self.args.conf_thresh,
                    device=self.device,
                    verbose=False
                )

                if track_results and track_results[0].boxes and track_results[0].boxes.id is not None:
                    boxes = track_results[0].boxes.xyxy.cpu().numpy()
                    track_ids = track_results[0].boxes.id.int().cpu().numpy()
                    confs = track_results[0].boxes.conf.cpu().numpy()

                    for box, track_id, v_conf in zip(boxes, track_ids, confs):
                        track_id = int(track_id)

                        vx1, vy1, vx2, vy2 = map(int, box)
                        vx1, vy1 = max(0, vx1), max(0, vy1)
                        vx2, vy2 = min(frame_width, vx2), min(frame_height, vy2)

                        vehicle_crop = frame[vy1:vy2, vx1:vx2]

                        # New vehicle entry
                        if track_id not in active_tracks:
                            active_tracks[track_id] = {
                                "entry_frame": frame_idx,
                                "last_seen_frame": frame_idx,
                                "last_ocr_frame": -999,
                                "ocr_reads": [],
                                "plate_bbox_found": False,
                                "best_plate": "DETECTING...",
                                "best_conf": 0.0,
                                "bbox": (vx1, vy1, vx2, vy2),
                                "best_vehicle_crop": vehicle_crop.copy() if vehicle_crop.size > 0 else None,
                                "best_vehicle_crop_area": vehicle_crop.shape[0] * vehicle_crop.shape[1] if vehicle_crop.size > 0 else 0,
                                "best_plate_crop": None,
                                "best_plate_area": 0
                            }
                            logger.info(
                                f"[{camera_id} | Frame {frame_idx:04d}] 🚗 Track #{track_id} "
                                f"entered view (Conf: {v_conf*100:.1f}%) at [{vx1},{vy1},{vx2},{vy2}]"
                            )
                        else:
                            active_tracks[track_id]["last_seen_frame"] = frame_idx
                            active_tracks[track_id]["bbox"] = (vx1, vy1, vx2, vy2)
                            
                            # Keep sharpest vehicle crop
                            if vehicle_crop.size > 0:
                                cur_area = vehicle_crop.shape[0] * vehicle_crop.shape[1]
                                if cur_area > active_tracks[track_id]["best_vehicle_crop_area"]:
                                    active_tracks[track_id]["best_vehicle_crop"] = vehicle_crop.copy()
                                    active_tracks[track_id]["best_vehicle_crop_area"] = cur_area

                        # Step 2: License Plate Detection & OCR Recognition
                        frames_since_ocr = frame_idx - active_tracks[track_id]["last_ocr_frame"]
                        has_enough_samples = len(active_tracks[track_id]["ocr_reads"]) >= self.args.max_ocr_samples

                        if (not has_enough_samples) and (frames_since_ocr >= self.args.ocr_interval):
                            active_tracks[track_id]["last_ocr_frame"] = frame_idx

                            if vehicle_crop.size > 0 and vehicle_crop.shape[0] > 20 and vehicle_crop.shape[1] > 20:
                                
                                # Run Plate Detection (No deprecated 'half' argument)
                                plate_results = self.plate_model.predict(
                                    source=vehicle_crop,
                                    conf=self.args.plate_conf_thresh,
                                    device=self.device,
                                    verbose=False
                                )

                                if plate_results and plate_results[0].boxes and len(plate_results[0].boxes) > 0:
                                    p_boxes = plate_results[0].boxes.xyxy.cpu().numpy()
                                    p_confs = plate_results[0].boxes.conf.cpu().numpy()

                                    best_p_idx = np.argmax(p_confs)
                                    px1, py1, px2, py2 = map(int, p_boxes[best_p_idx])
                                    best_p_conf = float(p_confs[best_p_idx])

                                    # Global plate coordinates for frame annotation
                                    global_px1, global_py1 = vx1 + px1, vy1 + py1
                                    global_px2, global_py2 = vx1 + px2, vy1 + py2
                                    current_frame_plates.append((global_px1, global_py1, global_px2, global_py2))

                                    # Switch state to RECOGNIZING...
                                    active_tracks[track_id]["plate_bbox_found"] = True
                                    if active_tracks[track_id]["best_plate"] == "DETECTING...":
                                        active_tracks[track_id]["best_plate"] = "RECOGNIZING..."

                                    # Pad in FRAME coordinates, not vehicle-crop coordinates.
                                    # Clamping the padding to the vehicle box silently ate it
                                    # whenever the plate sat at the edge of that box, which is
                                    # exactly where plates usually are — that was truncating
                                    # characters off the end of the crop.
                                    pad_x = max(6, int((px2 - px1) * self.args.plate_pad))
                                    pad_y = max(4, int((py2 - py1) * self.args.plate_pad))
                                    c_px1 = max(0, global_px1 - pad_x)
                                    c_py1 = max(0, global_py1 - pad_y)
                                    c_px2 = min(frame_width,  global_px2 + pad_x)
                                    c_py2 = min(frame_height, global_py2 + pad_y)

                                    plate_crop = frame[c_py1:c_py2, c_px1:c_px2]

                                    # Only process plates that have minimum resolution to be legible (height >= 16px, width >= 40px)
                                    if plate_crop.size > 0 and plate_crop.shape[0] >= 16 and plate_crop.shape[1] >= 40:
                                        # Run Multi-Pass PaddleOCR
                                        ocr_lines = self._run_ocr_inference(plate_crop, track_id, camera_id, frame_idx)

                                        if ocr_lines:
                                            for raw_text, ocr_score in ocr_lines:
                                                cleaned = clean_plate_text(raw_text)
                                                # Near-zero-confidence variants are noise; they
                                                # would still get a say in the length vote.
                                                if cleaned and len(cleaned) >= 4 and ocr_score >= 0.20:
                                                    active_tracks[track_id]["ocr_reads"].append((cleaned, ocr_score))
                                                    cur_best, cur_conf = resolve_best_plate(active_tracks[track_id]["ocr_reads"])
                                                    active_tracks[track_id]["best_plate"] = cur_best
                                                    active_tracks[track_id]["best_conf"] = cur_conf
                                                    
                                                    # Keep the LARGEST crop, not the one this
                                                    # OCR pass scored highest — scoring crops by
                                                    # the engine we're trying to evaluate is
                                                    # circular. More pixels on the plate is the
                                                    # signal that actually predicts legibility.
                                                    area = plate_crop.shape[0] * plate_crop.shape[1]
                                                    if area > active_tracks[track_id]["best_plate_area"]:
                                                        active_tracks[track_id]["best_plate_crop"] = plate_crop.copy()
                                                        active_tracks[track_id]["best_plate_area"] = area

                                                    logger.info(
                                                        f"[{camera_id} | Frame {frame_idx:04d}] ✅ Track #{track_id}: "
                                                        f"OCR Accepted -> '{cleaned}' (Score: {ocr_score*100:.1f}%) | "
                                                        f"Current Resolved: '{cur_best}' ({cur_conf:.1f}%)"
                                                    )
                                                else:
                                                    logger.info(
                                                        f"[{camera_id} | Frame {frame_idx:04d}] ⚠️ Track #{track_id}: "
                                                        f"Candidate '{raw_text}' discarded (length < 4 chars or noisy)"
                                                    )
                                        else:
                                            # If OCR failed, still maintain candidate plate crop if detection confidence was high
                                            area = plate_crop.shape[0] * plate_crop.shape[1]
                                            if best_p_conf > 0.40 and area > active_tracks[track_id]["best_plate_area"]:
                                                active_tracks[track_id]["best_plate_crop"] = plate_crop.copy()
                                                active_tracks[track_id]["best_plate_area"] = area

                # Step 3: Check for Dead Tracklets (Lost for max_lost_frames)
                dead_ids = [
                    t_id for t_id, t_data in active_tracks.items()
                    if frame_idx - t_data["last_seen_frame"] > self.args.max_lost_frames
                ]
                for t_id in dead_ids:
                    self._log_track_to_csv(camera_id, t_id, active_tracks[t_id], fps)
                    logged_count += 1
                    del active_tracks[t_id]

                # Step 4: Video Annotation
                if video_writer is not None:
                    annotated_frame = self._render_frame(
                        frame=frame,
                        active_tracks=active_tracks,
                        current_frame_plates=current_frame_plates,
                        camera_id=camera_id,
                        frame_idx=frame_idx,
                        total_frames=total_frames,
                        logged_count=logged_count,
                        fps=fps
                    )
                    video_writer.write(annotated_frame)

                # Frame progress update every 100 frames
                if frame_idx % 100 == 0 or frame_idx == total_frames:
                    elapsed = time.time() - start_time
                    fps_val = frame_idx / max(elapsed, 0.001)
                    pct = (frame_idx / max(total_frames, 1)) * 100.0
                    logger.info(
                        f"[{camera_id}] Progress: {frame_idx}/{total_frames} ({pct:.1f}%) | "
                        f"Rate: {fps_val:.1f} FPS | Active Tracks: {len(active_tracks)}"
                    )

        except KeyboardInterrupt:
            logger.warning(f"[{camera_id}] Interrupted by user. Finalizing buffer...")
        finally:
            # Flush any remaining active tracks
            for t_id, t_data in list(active_tracks.items()):
                self._log_track_to_csv(camera_id, t_id, t_data, fps)
                logged_count += 1
                del active_tracks[t_id]

            cap.release()
            if video_writer is not None:
                video_writer.release()
                logger.info(f"[{camera_id}] ✅ Annotated video saved: '{out_video_path}'")

        if self.device == "cuda":
            torch.cuda.empty_cache()

        duration = time.time() - start_time
        logger.info(
            f"[{camera_id}] Finished in {duration:.2f}s | "
            f"Avg Speed: {frame_idx / max(duration, 0.001):.1f} FPS | "
            f"Total Vehicles Logged: {logged_count}\n"
        )

    # --------------------------------------------------------------------------
    # Frame Visualization with 3-Stage Dynamic Bounding Box Tags
    # --------------------------------------------------------------------------
    def _render_frame(
        self,
        frame: np.ndarray,
        active_tracks: Dict[int, dict],
        current_frame_plates: List[Tuple[int, int, int, int]],
        camera_id: str,
        frame_idx: int,
        total_frames: int,
        logged_count: int,
        fps: float
    ) -> np.ndarray:
        """
        Render dynamic 3-stage bounding box tags:
        1. DETECTING...  (Orange) - Vehicle detected, searching for plate
        2. RECOGNIZING... (Yellow) - Plate bbox detected, running OCR
        3. [PLATE NUMBER] (Green)  - Number plate confirmed with confidence
        """
        vis_frame = frame.copy()
        h, w = vis_frame.shape[:2]

        # Every size below was hand-tuned against 1080p. CAM2 is 4K, so fixed
        # pixel sizes render at half the apparent size there. Scale all overlay
        # geometry off the frame height so the HUD looks the same on any feed.
        s = h / 1080.0
        px = lambda v: max(1, int(round(v * s)))        # scale a pixel distance
        fs = lambda v: v * s                             # scale a font size

        for track_id, t_data in active_tracks.items():
            if t_data["last_seen_frame"] == frame_idx:
                vx1, vy1, vx2, vy2 = t_data["bbox"]
                plate_str = t_data["best_plate"]
                conf = t_data["best_conf"]

                if plate_str not in ["DETECTING...", "RECOGNIZING...", "UNKNOWN"]:
                    box_color = (0, 220, 0)
                    tag_text = f"ID:{track_id} | {plate_str} ({conf:.0f}%)"
                    text_color = (0, 0, 0)
                elif plate_str == "RECOGNIZING...":
                    box_color = (0, 215, 255)
                    tag_text = f"ID:{track_id} | RECOGNIZING..."
                    text_color = (0, 0, 0)
                else:
                    box_color = (255, 140, 0)
                    tag_text = f"ID:{track_id} | DETECTING..."
                    text_color = (255, 255, 255)

                cv2.rectangle(vis_frame, (vx1, vy1), (vx2, vy2), box_color, px(2))

                tag_scale, tag_thick = fs(0.52), px(2)
                (tw, th), baseline = cv2.getTextSize(
                    tag_text, cv2.FONT_HERSHEY_SIMPLEX, tag_scale, tag_thick)
                lbl_y1 = max(0, vy1 - th - px(8))
                lbl_y2 = vy1
                lbl_x2 = min(w, vx1 + tw + px(10))

                cv2.rectangle(vis_frame, (vx1, lbl_y1), (lbl_x2, lbl_y2), box_color, -1)
                cv2.putText(
                    vis_frame,
                    tag_text,
                    (vx1 + px(5), vy1 - px(5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    tag_scale,
                    text_color,
                    tag_thick,
                    cv2.LINE_AA
                )

        # Draw detected license plate bounding boxes in current frame (Cyan outline)
        for bx1, by1, bx2, by2 in current_frame_plates:
            cv2.rectangle(vis_frame, (bx1, by1), (bx2, by2), (0, 255, 255), px(2))

        # Modern Top-Left HUD
        hud_w, hud_h, margin = px(360), px(110), px(15)
        overlay = vis_frame.copy()
        cv2.rectangle(overlay, (margin, margin),
                      (margin + hud_w, margin + hud_h), (18, 22, 28), -1)
        cv2.addWeighted(overlay, 0.78, vis_frame, 0.22, 0, vis_frame)
        cv2.rectangle(vis_frame, (margin, margin),
                      (margin + hud_w, margin + hud_h), (50, 60, 75), px(1))

        pct = (frame_idx / max(total_frames, 1)) * 100.0
        hud_lines = [
            (f"NODE: {camera_id} | ZYRODEV ANPR", 38, 0.52, (0, 200, 255), 2),
            (f"FRAME: {frame_idx}/{total_frames} ({pct:.1f}%)", 62, 0.44, (220, 220, 220), 1),
            (f"ACTIVE VEHICLES: {len(active_tracks)}", 84, 0.44, (100, 255, 100), 1),
            (f"VEHICLES LOGGED: {logged_count}", 106, 0.44, (255, 180, 50), 1),
        ]
        for text, y, t_scale, color, t_thick in hud_lines:
            cv2.putText(vis_frame, text, (px(26), px(y)), cv2.FONT_HERSHEY_SIMPLEX,
                        fs(t_scale), color, px(t_thick), cv2.LINE_AA)

        # Burnt-in recording timestamp, top-right, the way a DVR/RTSP feed shows it.
        # This is the clock the CSV entry/exit times are anchored to.
        stamp = self._wallclock(frame_idx, fps).strftime(OVERLAY_TS_FMT)
        font, scale, thick = cv2.FONT_HERSHEY_SIMPLEX, fs(0.62), px(2)
        (tw, th), base = cv2.getTextSize(stamp, font, scale, thick)
        x2, y1 = w - px(20), px(18)
        x1, y2 = x2 - tw - px(20), y1 + th + base + px(12)

        shade = vis_frame.copy()
        cv2.rectangle(shade, (x1, y1), (x2, y2), (0, 0, 0), -1)
        cv2.addWeighted(shade, 0.45, vis_frame, 0.55, 0, vis_frame)
        # Dark outline first so the text stays readable over a bright sky.
        org = (x1 + px(10), y2 - base - px(5))
        cv2.putText(vis_frame, stamp, org, font, scale, (0, 0, 0), thick + px(2), cv2.LINE_AA)
        cv2.putText(vis_frame, stamp, org, font, scale, (255, 255, 255), thick, cv2.LINE_AA)

        return vis_frame

    # --------------------------------------------------------------------------
    # Multi-Camera Sequential Runner
    # --------------------------------------------------------------------------
    def run(self, video_paths: List[str]):
        """Run pipeline across all input video files sequentially."""
        total = len(video_paths)
        logger.info(f"Initializing ANPR Processing Pipeline for {total} video stream(s)...")

        for idx, v_path in enumerate(video_paths, start=1):
            cam_id = f"Camera_{idx}"
            self.process_video_stream(v_path, cam_id)

        logger.info("\n" + "="*70)
        logger.info("🎉 ALL CAMERA FEEDS PROCESSED SUCCESSFULLY!")
        logger.info(f"📁 Consolidated CSV Log: {self.csv_log_path}")
        logger.info(f"📁 Verified Crops: {os.path.join(self.args.output_dir, 'crops')}")
        logger.info(f"📁 Output Video Directory: {self.args.output_dir}")
        logger.info("="*70)


# ==============================================================================
# CLI Entry Point
# ==============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="City-Wide Multi-Camera ANPR Trajectory Tracking and Urban Traffic Analytics"
    )
    parser.add_argument(
        "positional_videos",
        nargs="*",
        default=[],
        help="Optional positional list of video files"
    )
    parser.add_argument(
        "--videos",
        nargs="+",
        default=[],
        help="List of video files to process sequentially (e.g. --videos cam1.mp4 cam2.mp4)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./outputs",
        help="Directory to save output annotated videos, crops, and vehicle_logs.csv (default: ./outputs)"
    )
    parser.add_argument(
        "--vehicle_model",
        type=str,
        default="yolo11n.pt",
        help="YOLO model for vehicle tracking: 'yolo11n.pt' or 'yolov8n.pt' (default: yolo11n.pt)"
    )
    parser.add_argument(
        "--plate_model",
        type=str,
        default="yolov8n_plate.pt",
        help="Trained plate detector model weights (default: yolov8n_plate.pt)"
    )
    parser.add_argument(
        "--conf_thresh",
        type=float,
        default=0.35,
        help="Confidence threshold for vehicle detection (default: 0.35)"
    )
    parser.add_argument(
        "--plate_conf_thresh",
        type=float,
        default=0.25,
        help="Confidence threshold for plate detection (default: 0.25)"
    )
    parser.add_argument(
        "--ocr_interval",
        type=int,
        default=1,
        help="Run OCR every N frames for active vehicles (default: 1). Raising this to "
             "2-3 is close to free: the per-character vote still gets plenty of samples."
    )
    parser.add_argument(
        "--max_ocr_samples",
        type=int,
        default=40,
        help="Max OCR reads per vehicle before locking candidate pool (default: 40). "
             "Each frame contributes up to 4 reads (one per preprocessing variant), so "
             "this is roughly 10 frames of evidence for the per-character vote."
    )
    parser.add_argument(
        "--min_save_conf",
        type=float,
        default=25.0,
        help="Minimum OCR confidence percentage required to save vehicle/plate crops to disk (default: 40.0)"
    )
    parser.add_argument(
        "--max_lost_frames",
        type=int,
        default=30,
        help="Frames before finalizing an inactive tracklet (default: 30)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Compute device ('cuda', 'cpu', or leave blank for auto)"
    )
    parser.add_argument(
        "--no_video",
        action="store_true",
        help="Disable writing annotated MP4 videos for high-speed batch processing"
    )
    parser.add_argument(
        "--recorded_at",
        type=parse_recorded_at,
        default="2026-08-31 15:58:00",
        help="Wall-clock time the source footage started recording, shared by every "
             "camera (default: 2026-08-31 15:58:00). Burnt into the output video and "
             "used for the entry/exit timestamps in vehicle_logs.csv."
    )
    parser.add_argument(
        "--max_frames",
        type=int,
        default=0,
        help="Stop each feed after N frames (0 = whole video). Useful for quick demo runs."
    )
    parser.add_argument(
        "--plate_pad",
        type=float,
        default=0.25,
        help="Fractional padding added around the plate box, in frame coords (default: 0.25)"
    )
    parser.add_argument(
        "--state_prior",
        type=str,
        default="",
        help="Comma-separated state codes these cameras actually see (e.g. TN,KL,KA). "
             "Breaks ties when repairing a garbled state field."
    )

    return parser.parse_args()


def main():
    global STATE_PRIOR
    args = parse_args()

    STATE_PRIOR = tuple(s.strip().upper() for s in args.state_prior.split(",") if s.strip())
    if unknown := [s for s in STATE_PRIOR if s not in STATE_CODES]:
        logger.warning(f"Unknown state code(s) in --state_prior: {', '.join(unknown)}")

    all_videos = args.videos if args.videos else args.positional_videos
    if not all_videos:
        print("\n[ERROR] No video files provided!")
        print("Usage: python main.py --videos ./input2/CAM1_comp.mp4 --output_dir ./outputs\n")
        sys.exit(1)

    pipeline = MultiCameraANPRPipeline(args)
    pipeline.run(all_videos)


if __name__ == "__main__":
    main()
