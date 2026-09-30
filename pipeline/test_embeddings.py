#!/usr/bin/env python3
"""
Vehicle Re-ID Embedding Accuracy Evaluation & Cross-Camera Trajectory Tracking
=============================================================================
SIH Problem Statement: 26127 (Bharat Electronics Limited)

Modes of Operation:
1. Cross-Camera Trajectory Tracking by Image (--image <path> or --track <key>):
   Takes a vehicle crop from one camera, extracts its 512-d Re-ID embedding,
   searches for that vehicle across all other cameras in the network using cosine
   similarity, pulls chronological sighting metadata from 'vehicle_logs.csv',
   reconstructs the trajectory route (e.g. CAM4 -> CAM5 / CAM6 with transit times),
   and displays a visual multi-camera trajectory comparison pop-up.

2. Random Cross-Camera Tracking (--one [--camera <Camera_4>]):
   Picks a random vehicle crop (optionally from a specific camera) and tracks its
   journey across the other cameras.

3. Accuracy Benchmark (default, no flags):
   Evaluates all sample query crops against the gallery and outputs Top-1, Top-K,
   MRR, and separation margin metrics.

Usage Examples:
    # 1. Track a specific vehicle image across other cameras (filters AFTER query time by default)
    python pipeline/test_embeddings.py --image outputs_test/crops/vehicles/Camera_4_track_190.jpg

    # 2. Trace a specific track by name
    python pipeline/test_embeddings.py --track Camera_4_track_190

    # 3. Pick a random vehicle from Camera_4 and trace downstream sightings
    python pipeline/test_embeddings.py --one --camera Camera_4

    # 4. Search for a custom image with explicit reference time
    python pipeline/test_embeddings.py --image path/to/vehicle.jpg --time "15:58:20"

    # 5. Filter matches strictly to an explicit time range
    python pipeline/test_embeddings.py --image path/to/vehicle.jpg --time_range "15:58:20, 16:01:00"

    # 6. Disable temporal filter and match across all recorded times
    python pipeline/test_embeddings.py --one --all_times

    # 7. Full benchmark across all sample crops
    python pipeline/test_embeddings.py
"""

import os
import sys
import glob
import re
import random
import argparse
import time
import difflib
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

import cv2
import numpy as np

# Ensure pipeline/ and repo root are on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
for path in (REPO_ROOT, SCRIPT_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from reid import get_reid_model

TS_FMT = "%Y-%m-%d %H:%M:%S.%f"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark Re-ID Embeddings and Track Vehicles Across Multiple Cameras"
    )
    parser.add_argument(
        "--image",
        type=str,
        default="",
        help="Path to a vehicle crop image to track across other cameras"
    )
    parser.add_argument(
        "--track",
        type=str,
        default="",
        help="Track key to trace across cameras (e.g. --track Camera_4_track_190)"
    )
    parser.add_argument(
        "--one",
        action="store_true",
        help="Pick one random vehicle crop and track its cross-camera trajectory"
    )
    parser.add_argument(
        "--camera",
        type=str,
        default="",
        help="Filter origin camera when picking random query with --one (e.g. --camera Camera_4)"
    )
    parser.add_argument(
        "--cross_camera",
        action="store_true",
        default=True,
        help="Perform cross-camera trajectory tracking (default: True)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./outputs",
        help="Base output directory from main.py (default: ./outputs, auto-checks ./outputs_test)"
    )
    parser.add_argument(
        "--crops_dir",
        type=str,
        default="",
        help="Path to gallery vehicle crops and .npy embeddings (defaults to <output_dir>/crops/vehicles)"
    )
    parser.add_argument(
        "--samples_dir",
        type=str,
        default="",
        help="Path to query sample crops (defaults to <output_dir>/sample_crops)"
    )
    parser.add_argument(
        "--csv_path",
        type=str,
        default="",
        help="Path to vehicle_logs.csv (defaults to <output_dir>/vehicle_logs.csv)"
    )
    parser.add_argument(
        "--save_path",
        type=str,
        default="",
        help="Custom path to save the visual trajectory image (defaults to <output_dir>/reid_trajectory_result.jpg)"
    )
    parser.add_argument(
        "--no_popup",
        action="store_true",
        help="Do not display the GUI pop-up window (useful in headless/automated test environments)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="veri776",
        help="Re-ID feature extractor model: 'veri776' (SOTA VeRi-776 Re-ID), 'dinov2', 'resnet50', 'resnet18' (default: veri776)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Compute device ('cuda', 'cpu', or leave blank for auto)"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=64,
        help="Batch size for benchmark evaluation (default: 64)"
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=5,
        help="Top-K nearest neighbors cutoff (default: 5)"
    )
    parser.add_argument(
        "--top_n",
        type=int,
        default=1,
        help="Number of matched candidates to display (default: 1 for clean single optimal path; use --top_n 5 to view candidate gallery)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed match logs"
    )
    # Temporal filtering arguments
    parser.add_argument(
        "--time",
        type=str,
        default="",
        help="Sighting timestamp of the query image (e.g. '15:58:20' or '2026-08-31 15:58:20')"
    )
    parser.add_argument(
        "--time_range",
        type=str,
        default="",
        help="Explicit time window to search for matches 'start,end' (e.g. '15:58:20,16:01:00')"
    )
    parser.add_argument(
        "--start_time",
        type=str,
        default="",
        help="Explicit start timestamp to search for matches (e.g. '15:58:20')"
    )
    parser.add_argument(
        "--end_time",
        type=str,
        default="",
        help="Explicit end timestamp to search for matches (e.g. '16:01:00')"
    )
    parser.add_argument(
        "--forward_only",
        action="store_true",
        default=False,
        help="Search only forward (after query sighting time). Default: False (searches both ways / bidirectional)."
    )
    parser.add_argument(
        "--after",
        action="store_true",
        dest="forward_only",
        help="Alias for --forward_only: search only after query sighting time"
    )
    parser.add_argument(
        "--max_gap",
        type=float,
        default=300.0,
        help="Maximum forward transit gap in seconds after query image (default: 300.0s = 5 mins)"
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=2.0,
        help="Clock tolerance buffer in seconds before query sighting (default: 2.0s)"
    )
    parser.add_argument(
        "--all_times",
        action="store_true",
        default=False,
        help="Disable temporal filtering and search across all recorded timestamps (default: False)"
    )
    return parser.parse_args()


# =========================================================================
#  DIRECTORY & METADATA RESOLUTION
# =========================================================================

def resolve_output_dirs(output_dir: str, crops_dir: str, samples_dir: str, csv_path: str) -> Tuple[str, str, str, str]:
    """
    Resolve and auto-detect gallery crops, sample queries, and vehicle_logs.csv.
    """
    candidate_crops = crops_dir or os.path.join(output_dir, "crops", "vehicles")
    candidate_samples = samples_dir or os.path.join(output_dir, "sample_crops")
    candidate_csv = csv_path or os.path.join(output_dir, "vehicle_logs.csv")

    if os.path.isdir(candidate_crops) and glob.glob(os.path.join(candidate_crops, "*_emb.npy")):
        return output_dir, candidate_crops, candidate_samples, candidate_csv

    # Auto-detect alternatives e.g. outputs_test
    search_dirs = ["./outputs_test", "./outputs"] + sorted(glob.glob("./output*"))
    seen = set()
    for base in search_dirs:
        if base in seen:
            continue
        seen.add(base)
        t_crops = os.path.join(base, "crops", "vehicles")
        t_samples = os.path.join(base, "sample_crops")
        t_csv = os.path.join(base, "vehicle_logs.csv")
        if os.path.isdir(t_crops) and glob.glob(os.path.join(t_crops, "*_emb.npy")):
            print(f"ℹ️  [Auto-Detect] Found gallery embeddings in '{t_crops}'. Using base directory: {base}")
            return base, (crops_dir or t_crops), (samples_dir or t_samples), (csv_path or t_csv)

    return output_dir, candidate_crops, candidate_samples, candidate_csv


def load_csv_metadata(csv_path: str) -> Dict[str, dict]:
    """
    Load vehicle_logs.csv into a dictionary keyed by '<camera_id>_track_<track_id>'.
    """
    if not os.path.isfile(csv_path):
        return {}

    import csv
    meta = {}
    with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get("camera_id", "").strip()
            tid = row.get("track_id", "").strip()
            if cid and tid:
                key = f"{cid}_track_{tid}"
                meta[key] = {
                    "camera_id": cid,
                    "track_id": int(tid) if tid.isdigit() else tid,
                    "entry_timestamp": row.get("entry_timestamp", ""),
                    "exit_timestamp": row.get("exit_timestamp", ""),
                    "plate_number": row.get("plate_number", "UNKNOWN").strip().upper(),
                    "average_ocr_confidence": float(row.get("average_ocr_confidence") or 0.0),
                    "entry_offset_sec": float(row.get("entry_offset_sec") or 0.0),
                    "exit_offset_sec": float(row.get("exit_offset_sec") or 0.0),
                    "embedding_path": row.get("embedding_path", "").strip()
                }
    return meta


def load_gallery_by_camera(crops_dir: str) -> Tuple[Dict[str, List[str]], Dict[str, np.ndarray], Dict[str, str]]:
    """
    Load gallery vehicle embeddings partitioned by camera ID.
    Returns:
        camera_keys: dict mapping camera_id -> list of vehicle keys
        camera_matrices: dict mapping camera_id -> (N, 512) normalized numpy array
        crop_images: dict mapping key -> image path
    """
    if not os.path.isdir(crops_dir):
        return {}, {}, {}

    emb_files = sorted(glob.glob(os.path.join(crops_dir, "*_emb.npy")))
    camera_keys = defaultdict(list)
    camera_embs = defaultdict(list)
    crop_images = {}

    for fpath in emb_files:
        fname = os.path.basename(fpath)
        key = fname[:-8] if fname.endswith("_emb.npy") else os.path.splitext(fname)[0]

        # Extract camera_id (e.g. "Camera_1_track_12" -> "Camera_1")
        if "_track_" in key:
            cam_id = key.split("_track_")[0]
        else:
            cam_id = "Default"

        try:
            vec = np.load(fpath).astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            else:
                continue
        except Exception:
            continue

        img_path = os.path.join(crops_dir, f"{key}.jpg")
        camera_keys[cam_id].append(key)
        camera_embs[cam_id].append(vec)
        crop_images[key] = img_path if os.path.exists(img_path) else ""

    camera_matrices = {}
    for cam, embs in camera_embs.items():
        camera_matrices[cam] = np.array(embs, dtype=np.float32)

    return dict(camera_keys), camera_matrices, crop_images


def parse_timestamp(ts_str: Optional[str], default_date: str = "2026-08-31") -> Optional[datetime]:
    if not ts_str:
        return None
    ts_str = str(ts_str).strip()
    if not ts_str:
        return None

    # If only time was provided (e.g. '15:58:20' or '15:58:20.200'), prefix default date
    if " " not in ts_str and "T" not in ts_str and "-" not in ts_str:
        ts_str = f"{default_date} {ts_str}"

    for fmt in (TS_FMT, "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            pass
    return None


# =========================================================================
#  VISUALIZATION & POP-UP RENDERING
# =========================================================================

def letterbox_image(image: Optional[np.ndarray], target_w: int, target_h: int, bg_color=(24, 25, 32)) -> np.ndarray:
    """Resize image preserving aspect ratio with centered background padding."""
    if image is None or image.size == 0:
        canvas = np.full((target_h, target_w, 3), bg_color, dtype=np.uint8)
        cv2.putText(canvas, "No Image", (max(10, target_w // 4), target_h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 135), 1, cv2.LINE_AA)
        return canvas

    h, w = image.shape[:2]
    scale = min(target_w / max(w, 1), target_h / max(h, 1))
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = np.full((target_h, target_w, 3), bg_color, dtype=np.uint8)
    x_off = (target_w - new_w) // 2
    y_off = (target_h - new_h) // 2
    canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
    return canvas


def format_transit_details(gap_sec: Optional[float], query_cam: Optional[str], cand_cam: str) -> dict:
    """
    Format bidirectional transit time and direction.
    Returns: dict with label, direction ('Incoming'/'Outgoing'/'Concurrent'/'Unknown'), route, color
    """
    q_name = query_cam.replace("Camera_", "CAM") if query_cam else "QUERY"
    c_name = cand_cam.replace("Camera_", "CAM")

    if gap_sec is None:
        return {
            "label": "Time: N/A",
            "direction": "Unknown",
            "route": f"{c_name} <-> {q_name}",
            "color": (160, 160, 175)
        }

    if gap_sec > 1.0:
        return {
            "label": f"Outgoing (+{gap_sec:.1f}s)",
            "direction": "Outgoing",
            "route": f"{q_name} -> {c_name}",
            "color": (80, 220, 100)  # Green
        }
    elif gap_sec < -1.0:
        return {
            "label": f"Incoming (-{abs(gap_sec):.1f}s)",
            "direction": "Incoming",
            "route": f"{c_name} -> {q_name}",
            "color": (80, 210, 255)  # Cyan
        }
    else:
        return {
            "label": f"Concurrent ({gap_sec:+.1f}s)",
            "direction": "Concurrent",
            "route": f"{q_name} ~ {c_name}",
            "color": (255, 215, 0)   # Gold
        }


def render_match_card(canvas: np.ndarray, x: int, y: int, w: int, h: int,
                      rank: int,
                      title: str,
                      sub_title: str,
                      image: Optional[np.ndarray],
                      details: List[Tuple[str, Tuple[int, int, int]]],
                      border_color: Tuple[int, int, int],
                      border_thick: int = 2,
                      is_query: bool = False,
                      is_top1: bool = False):
    """Draws an individual vehicle card (Query card or Candidate match card)."""
    # Card Background
    bg_color = (36, 38, 48) if is_top1 else ((32, 34, 42) if is_query else (28, 29, 37))
    cv2.rectangle(canvas, (x, y), (x + w, y + h), bg_color, -1)

    # Header bar
    hdr_h = 52
    hdr_bg = (44, 48, 62) if is_top1 else ((38, 42, 54) if is_query else (32, 34, 44))
    cv2.rectangle(canvas, (x, y), (x + w, y + hdr_h), hdr_bg, -1)
    cv2.line(canvas, (x, y + hdr_h), (x + w, y + hdr_h), (55, 60, 75), 1)

    # Header Titles
    title_col = (100, 255, 120) if is_top1 else ((255, 220, 100) if is_query else (255, 255, 255))
    cv2.putText(canvas, title, (x + 10, y + 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.44, title_col, 2, cv2.LINE_AA)

    sub_col = (180, 210, 240) if is_top1 else (160, 170, 185)
    cv2.putText(canvas, sub_title, (x + 10, y + 43),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, sub_col, 1, cv2.LINE_AA)

    # Image section
    img_pad = 6
    img_x = x + img_pad
    img_y = y + hdr_h + img_pad
    img_w = w - (img_pad * 2)
    img_h = 165

    letterboxed = letterbox_image(image, img_w, img_h)
    canvas[img_y:img_y + img_h, img_x:img_x + img_w] = letterboxed

    # Image inner border
    cv2.rectangle(canvas, (img_x, img_y), (img_x + img_w, img_y + img_h), (50, 54, 68), 1)

    # Details Section
    dtl_y = img_y + img_h + img_pad + 6
    cv2.line(canvas, (x, dtl_y - 6), (x + w, dtl_y - 6), (48, 52, 65), 1)

    cur_line_y = dtl_y + 14
    for line_text, line_color in details:
        cv2.putText(canvas, line_text, (x + 10, cur_line_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, line_color, 1, cv2.LINE_AA)
        cur_line_y += 21

    # Outer Card border
    cv2.rectangle(canvas, (x, y), (x + w, y + h), border_color, border_thick)


def build_multi_match_canvas(query_card_data: Dict,
                             matches: List[Dict],
                             route_summary: str,
                             save_path: str,
                             rejected_hop: Optional[Dict] = None,
                             time_filter_label: str = "") -> np.ndarray:
    """
    Constructs an interactive multi-camera visual dashboard displaying:
    - Leftmost card: Query vehicle crop with telemetry and origin metadata
    - Rightward cards: Top candidate matches ranked across other cameras,
      showing vehicle crops, rank badges, Re-ID similarity, color consistency %,
      transit direction (Incoming / Outgoing), and plate match info.
    """
    num_matches = len(matches)
    total_cards = 1 + num_matches

    # Responsive card sizing: clean, large cards for optimal 1-match view, compact for multi-match
    if num_matches <= 1:
        card_w = 330
        card_h = 475
        gap = 32
        margin_x = 36
    else:
        card_w = 255
        card_h = 450
        gap = 16
        margin_x = 24

    header_h = 88
    footer_h = 38

    total_w = max(800, (margin_x * 2) + (total_cards * card_w) + ((total_cards - 1) * gap))
    total_h = header_h + card_h + footer_h

    canvas = np.full((total_h, total_w, 3), (20, 21, 28), dtype=np.uint8)

    # --- Top Banner ---
    cv2.rectangle(canvas, (0, 0), (total_w, header_h), (14, 15, 21), -1)
    cv2.line(canvas, (0, header_h), (total_w, header_h), (45, 49, 62), 1)

    title_str = "VEHICLE RE-IDENTIFICATION & MULTI-CAMERA TRAJECTORY MATCHING"
    cv2.putText(canvas, title_str, (margin_x, 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA)

    time_str = f" | {time_filter_label}" if time_filter_label else ""
    if num_matches <= 1:
        sub_info = f"Reconstructed Route: {route_summary}{time_str}"
    else:
        sub_info = f"Route: {route_summary}{time_str} | Showing Top-{num_matches} Matches"
    cv2.putText(canvas, sub_info, (margin_x, 62),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (110, 215, 255), 1, cv2.LINE_AA)

    # Badges on top right
    pill_offset_x = total_w - margin_x

    # Badge 1: Top match status pill
    if num_matches > 0:
        top1 = matches[0]
        if top1.get("is_confirmed"):
            top1_txt = f" CONFIRMED: {top1['camera_id']} #{top1['track_id']} "
            top1_bg = (35, 140, 35)
        elif top1.get("composite_score", 0) >= 0.78:
            top1_txt = f" BEST MATCH: {top1['camera_id']} #{top1['track_id']} "
            top1_bg = (25, 120, 180)
        else:
            top1_txt = " NO CONFIRMED SIGHTING (<0.78) "
            top1_bg = (30, 80, 180)

        (tw, th), _ = cv2.getTextSize(top1_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.44, 2)
        px2 = pill_offset_x
        px1 = px2 - tw - 14
        py1 = 18
        py2 = 18 + th + 16
        cv2.rectangle(canvas, (px1, py1), (px2, py2), top1_bg, -1)
        cv2.rectangle(canvas, (px1, py1), (px2, py2), (255, 255, 255), 1)
        cv2.putText(canvas, top1_txt, (px1 + 7, py2 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 2, cv2.LINE_AA)
        pill_offset_x = px1 - 12

    # Badge 2: Temporal Filter Pill
    if "BIDIRECTIONAL" in time_filter_label:
        badge_txt = " BIDIRECTIONAL "
        badge_bg = (20, 110, 100)
    elif "FORWARD" in time_filter_label or "AFTER" in time_filter_label:
        badge_txt = " FORWARD ONLY "
        badge_bg = (20, 90, 140)
    elif "TIME" in time_filter_label:
        badge_txt = " TIME FILTERED "
        badge_bg = (80, 50, 120)
    else:
        badge_txt = " ALL TIMES "
        badge_bg = (40, 50, 70)

    (bw, bh), _ = cv2.getTextSize(badge_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
    bx2 = pill_offset_x
    bx1 = bx2 - bw - 12
    by1 = 20
    by2 = 20 + bh + 14
    cv2.rectangle(canvas, (bx1, by1), (bx2, by2), badge_bg, -1)
    cv2.rectangle(canvas, (bx1, by1), (bx2, by2), (100, 180, 255), 1)
    cv2.putText(canvas, badge_txt, (bx1 + 6, by2 - 7),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 230, 255), 1, cv2.LINE_AA)

    # --- Draw Card 0: Query Vehicle ---
    card_y = header_h + 12
    cur_x = margin_x

    q_cam = query_card_data.get("camera_id", "External")
    q_track = query_card_data.get("track_id", "N/A")
    q_plate = query_card_data.get("plate", "UNKNOWN")
    q_conf = query_card_data.get("conf", 0.0)
    q_entry = query_card_data.get("entry_ts", "N/A")
    q_exit = query_card_data.get("exit_ts", "N/A")
    q_dur = query_card_data.get("duration", 0.0)
    q_img = query_card_data.get("img")

    q_entry_short = q_entry.split(" ")[-1][:8] if " " in q_entry else q_entry
    q_exit_short = q_exit.split(" ")[-1][:8] if " " in q_exit else q_exit

    time_disp = f"Time: {q_entry_short} -> {q_exit_short}" if q_entry != "N/A" else "Time: Unspecified"
    filter_disp = f"Filter: {time_filter_label[:22]}" if time_filter_label else "Filter: All Times"

    q_details = [
        (f"Track ID: #{q_track}", (220, 220, 230)),
        (f"Plate: {q_plate} ({q_conf:.0f}%)" if q_plate != "UNKNOWN" else "Plate: UNKNOWN",
         (255, 215, 0) if q_plate != "UNKNOWN" else (160, 160, 175)),
        (time_disp, (180, 200, 220)),
        (f"Duration: {q_dur:.1f}s in feed" if q_dur > 0 else "Duration: Single snapshot", (170, 180, 195)),
        (f"Corridor: {q_cam} (Origin)", (100, 220, 255)),
        ("Role: Baseline Query", (100, 220, 255)),
        (filter_disp, (150, 200, 240)),
    ]

    render_match_card(
        canvas=canvas,
        x=cur_x,
        y=card_y,
        w=card_w,
        h=card_h,
        rank=0,
        title="[QUERY VEHICLE]",
        sub_title=f"{q_cam} | Track #{q_track}",
        image=q_img,
        details=q_details,
        border_color=(235, 175, 45),  # Cyan
        border_thick=2,
        is_query=True,
        is_top1=False
    )

    cur_x += card_w + gap

    # If no candidates matched the temporal filter
    if num_matches == 0:
        no_x = cur_x
        no_w = 440
        cv2.rectangle(canvas, (no_x, card_y), (no_x + no_w, card_y + card_h), (28, 29, 37), -1)
        cv2.rectangle(canvas, (no_x, card_y), (no_x + no_w, card_y + card_h), (60, 65, 80), 2)
        cv2.putText(canvas, "NO CANDIDATES IN TIME WINDOW", (no_x + 18, card_y + 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 120, 120), 2, cv2.LINE_AA)
        cv2.putText(canvas, f"Filter: {time_filter_label}", (no_x + 18, card_y + 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 190, 210), 1, cv2.LINE_AA)
        cv2.putText(canvas, "No downstream sightings recorded in this window.", (no_x + 18, card_y + 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (140, 150, 170), 1, cv2.LINE_AA)
        cv2.putText(canvas, "Vehicle may have parked or exited network.", (no_x + 18, card_y + 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (140, 150, 170), 1, cv2.LINE_AA)
        cv2.putText(canvas, "Try extending --max_gap or using --all_times.", (no_x + 18, card_y + 185),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 200, 255), 1, cv2.LINE_AA)

    # --- Draw Match Cards 1 to N ---
    for idx, match in enumerate(matches, start=1):
        m_cam = match["camera_id"]
        m_track = match.get("track_id", "N/A")
        m_sim = match.get("sim", 0.0)
        m_comp = match.get("composite_score", 0.0)
        m_plate = match.get("plate", "UNKNOWN")
        m_conf = match.get("ocr_conf", 0.0)
        m_color = match.get("color_sim", 0.5)
        m_transit = match.get("transit", {})
        m_img = match.get("img")
        m_entry = match.get("entry_ts", "N/A")
        m_exit = match.get("exit_ts", "N/A")
        m_confirmed = match.get("is_confirmed", False)
        m_plate_matched = match.get("plate_matched", False)

        m_entry_s = m_entry.split(" ")[-1][:8] if " " in m_entry else m_entry
        m_exit_s = m_exit.split(" ")[-1][:8] if " " in m_exit else m_exit

        is_top1 = (idx == 1)

        # Border color
        if is_top1:
            if m_confirmed or m_comp >= 0.78:
                border_col = (50, 220, 50)  # Bright Green
                border_th = 3
            else:
                border_col = (30, 160, 240)  # Amber
                border_th = 2
            if num_matches == 1:
                card_title = f"OPTIMAL MATCH [{m_cam}]" if (m_confirmed or m_comp >= 0.78) else f"BEST CANDIDATE [{m_cam}]"
            else:
                card_title = f"RANK #{idx} [BEST MATCH]"
        else:
            border_col = (70, 75, 95)
            border_th = 2
            card_title = f"RANK #{idx} [CANDIDATE]"

        # Colors for details
        sim_col = (50, 220, 50) if m_sim >= 0.85 else ((255, 215, 0) if m_sim >= 0.80 else (30, 150, 255))
        col_col = (80, 230, 100) if m_color >= 0.80 else ((220, 220, 120) if m_color >= 0.65 else (80, 80, 230))
        plate_col = (80, 230, 100) if m_plate_matched else ((255, 215, 0) if m_plate != "UNKNOWN" else (160, 160, 175))

        t_lbl = m_transit.get("label", "N/A")
        t_col = m_transit.get("color", (170, 180, 195))
        t_route = m_transit.get("route", f"{q_cam} <-> {m_cam}")

        m_details = [
            (f"Track ID: #{m_track} ({m_cam})", (220, 220, 230)),
            (f"Plate: {m_plate} ({m_conf:.0f}%)" if m_plate != "UNKNOWN" else "Plate: UNKNOWN", plate_col),
            (f"Re-ID Sim: {m_sim:.4f}", sim_col),
            (f"Color Sim: {m_color * 100:.1f}% ({'Match' if m_color >= 0.70 else 'Diff'})", col_col),
            (f"Transit: {t_lbl}", t_col),
            (f"Route: {t_route}", (170, 190, 220)),
            (f"Time: {m_entry_s} -> {m_exit_s}", (160, 170, 185)),
        ]

        render_match_card(
            canvas=canvas,
            x=cur_x,
            y=card_y,
            w=card_w,
            h=card_h,
            rank=idx,
            title=card_title,
            sub_title=f"{m_cam} | Score: {m_comp:.3f}",
            image=m_img,
            details=m_details,
            border_color=border_col,
            border_thick=border_th,
            is_query=False,
            is_top1=is_top1
        )

        cur_x += card_w + gap

    # --- Bottom Footer ---
    ftr_bar_y = total_h - footer_h
    cv2.rectangle(canvas, (0, ftr_bar_y), (total_w, total_h), (14, 15, 21), -1)
    cv2.line(canvas, (0, ftr_bar_y), (total_w, ftr_bar_y), (45, 49, 62), 1)

    hint_text = "Press any key in pop-up window or ESC to close. | Visual Saved to: " + os.path.basename(save_path)
    cv2.putText(canvas, hint_text, (margin_x, ftr_bar_y + 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.40, (150, 155, 170), 1, cv2.LINE_AA)

    # Save to disk
    os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
    cv2.imwrite(save_path, canvas)

    return canvas


build_cross_camera_trajectory_canvas = build_multi_match_canvas


def display_popup(canvas: np.ndarray, save_path: str, title: str = "Vehicle Trajectory Result", no_popup: bool = False):
    """Open GUI pop-up window if display is available."""
    print(f"\n🖼️  Visual comparison saved to: {save_path}")
    if no_popup:
        print("ℹ️  [--no_popup] Pop-up window display suppressed.")
        return

    has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    if not has_display:
        print("ℹ️  No graphical display ($DISPLAY / $WAYLAND_DISPLAY) detected. Skipped GUI window pop-up.")
        print(f"    Open '{save_path}' to view the visual match comparison.")
        return

    try:
        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        win_w = min(canvas.shape[1], 1600)
        win_h = min(canvas.shape[0], 900)
        cv2.resizeWindow(title, win_w, win_h)
        cv2.imshow(title, canvas)
        print("👀 Pop-up window opened! Press any key or close the window to continue...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"ℹ️  Could not open pop-up window ({e}).")
        print(f"    Visual result is saved at: {save_path}")


# =========================================================================
#  COLOR CONSISTENCY & RE-ID GATING HELPERS
# =========================================================================

def extract_color_histogram(img: Optional[np.ndarray]) -> np.ndarray:
    """
    Extract normalized HSV color histogram focusing on the central vehicle body
    to eliminate background road, sky, and vegetation.
    """
    if img is None or img.size == 0:
        return np.zeros(16, dtype=np.float32)
    h, w = img.shape[:2]
    # Sample central 60% of crop to exclude surrounding road
    crop = img[int(h * 0.2):int(h * 0.8), int(w * 0.2):int(w * 0.8)]
    if crop.size == 0:
        crop = img
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    # 8 Hue bins (color), 4 Saturation bins (color purity), 4 Value bins (brightness)
    h_hist = cv2.calcHist([hsv], [0], None, [8], [0, 180]).flatten()
    s_hist = cv2.calcHist([hsv], [1], None, [4], [0, 256]).flatten()
    v_hist = cv2.calcHist([hsv], [2], None, [4], [0, 256]).flatten()

    hist = np.concatenate([h_hist, s_hist, v_hist])
    norm = np.linalg.norm(hist)
    return hist / norm if norm > 0 else hist


def compute_color_similarity(img1: Optional[np.ndarray], img2: Optional[np.ndarray]) -> float:
    """Compute cosine similarity of normalized color histograms (range: 0 to 1)."""
    if img1 is None or img2 is None:
        return 0.5
    h1 = extract_color_histogram(img1)
    h2 = extract_color_histogram(img2)
    return float(np.dot(h1, h2))


# =========================================================================
#  CROSS-CAMERA TRAJECTORY MATCHING CORE
# =========================================================================

def track_cross_camera_trajectory(reid_model, query_img_path: str,
                                  camera_keys: Dict[str, List[str]],
                                  camera_matrices: Dict[str, np.ndarray],
                                  crop_images: Dict[str, str],
                                  csv_metadata: Dict[str, dict],
                                  output_dir: str = "./outputs",
                                  no_popup: bool = False,
                                  custom_save_path: str = "",
                                  top_n: int = 1,
                                  query_time: str = "",
                                  time_range: str = "",
                                  start_time: str = "",
                                  end_time: str = "",
                                  forward_only: bool = False,
                                  max_gap_sec: float = 300.0,
                                  tolerance_sec: float = 2.0,
                                  all_times: bool = False):
    """
    Given a query image from one camera, searches for the matching vehicle across
    other cameras in both directions (incoming and outgoing), enforcing the 2-camera
    network topology constraint (a vehicle can only appear in AT MOST 2 cameras, never all 3).
    Pre-filters candidate embeddings chronologically based on sighting timestamps or user window,
    ranks optimal matches across the network with Re-ID feature similarity, color consistency gating,
    and bidirectional transit times, and visualizes the reconstructed trajectory.
    """
    if not os.path.exists(query_img_path):
        print(f"\n[ERROR] Query image does not exist: {query_img_path}")
        sys.exit(1)

    query_img = cv2.imread(query_img_path)
    if query_img is None or query_img.size == 0:
        print(f"\n[ERROR] Could not load image: {query_img_path}")
        sys.exit(1)

    # 0. Auto-detect base date from CSV telemetry if present
    base_date = "2026-08-31"
    for m in csv_metadata.values():
        ts = m.get("entry_timestamp", "")
        if ts and len(ts) >= 10 and ts[4] == '-' and ts[7] == '-':
            base_date = ts[:10]
            break

    # 1. Determine origin camera & track ID from path if available
    query_key = None
    query_cam = None
    for cam in camera_keys:
        if cam in query_img_path:
            query_cam = cam
            for k in camera_keys[cam]:
                if k in query_img_path:
                    query_key = k
                    break
            break

    # 2. Extract Query Embedding
    q_emb = np.array(reid_model.get_embedding(query_img), dtype=np.float32)
    norm = np.linalg.norm(q_emb)
    if norm > 0:
        q_emb = q_emb / norm

    # 3. Pull Query Metadata & Resolve Reference Sighting Timestamp
    query_meta = csv_metadata.get(query_key, {}) if query_key else {}
    q_plate = query_meta.get("plate_number", "UNKNOWN").strip().upper()
    query_entry_dt = parse_timestamp(query_meta.get("entry_timestamp", ""), default_date=base_date)
    query_exit_dt = parse_timestamp(query_meta.get("exit_timestamp", ""), default_date=base_date)
    q_dur = 0.0
    if query_meta:
        q_dur = float(query_meta.get("exit_offset_sec") or 0.0) - float(query_meta.get("entry_offset_sec") or 0.0)

    # Reference timestamp for query sighting
    ref_dt = None
    if query_time:
        ref_dt = parse_timestamp(query_time, default_date=base_date)
    elif query_entry_dt:
        ref_dt = query_entry_dt
    elif query_exit_dt:
        ref_dt = query_exit_dt

    # 3b. Determine Temporal Filtering Window [t_min, t_max]
    t_min: Optional[datetime] = None
    t_max: Optional[datetime] = None
    time_filter_label = ""
    filter_mode_desc = ""

    if all_times:
        t_min = None
        t_max = None
        time_filter_label = "ALL TIMES"
        filter_mode_desc = "ALL TIMES (--all_times specified, matching across full timeline)"
    elif time_range:
        parts = [p.strip() for p in re.split(r'[,;]|\s+to\s+', time_range) if p.strip()]
        if len(parts) >= 2:
            t_min = parse_timestamp(parts[0], default_date=base_date)
            t_max = parse_timestamp(parts[1], default_date=base_date)
        elif len(parts) == 1:
            t_min = parse_timestamp(parts[0], default_date=base_date)
            t_max = t_min + timedelta(seconds=max_gap_sec) if t_min else None
        time_filter_label = f"TIME RANGE: {t_min.strftime('%H:%M:%S') if t_min else '*'} -> {t_max.strftime('%H:%M:%S') if t_max else '*'}"
        filter_mode_desc = f"EXPLICIT TIME RANGE ({time_filter_label})"
    elif start_time or end_time:
        t_min = parse_timestamp(start_time, default_date=base_date) if start_time else None
        t_max = parse_timestamp(end_time, default_date=base_date) if end_time else None
        if t_min and not t_max:
            t_max = t_min + timedelta(seconds=max_gap_sec)
        elif t_max and not t_min:
            t_min = t_max - timedelta(seconds=max_gap_sec)
        time_filter_label = f"TIME WINDOW: {t_min.strftime('%H:%M:%S') if t_min else '*'} -> {t_max.strftime('%H:%M:%S') if t_max else '*'}"
        filter_mode_desc = f"EXPLICIT TIME WINDOW ({time_filter_label})"
    elif ref_dt is not None:
        if forward_only:
            t_min = ref_dt - timedelta(seconds=tolerance_sec)
            t_max = ref_dt + timedelta(seconds=max_gap_sec)
            time_filter_label = f"FORWARD ONLY: {ref_dt.strftime('%H:%M:%S')} -> {t_max.strftime('%H:%M:%S')} (+{int(max_gap_sec)}s)"
            filter_mode_desc = f"FORWARD ONLY (After Query: {ref_dt.strftime('%H:%M:%S')} +{max_gap_sec:.0f}s, tolerance -{tolerance_sec:.1f}s)"
        else:
            # Default: Bidirectional search both ways (both incoming from and outgoing to connected cameras)
            t_min = ref_dt - timedelta(seconds=max_gap_sec)
            t_max = ref_dt + timedelta(seconds=max_gap_sec)
            time_filter_label = f"BIDIRECTIONAL: {t_min.strftime('%H:%M:%S')} <-> {t_max.strftime('%H:%M:%S')} (±{int(max_gap_sec)}s)"
            filter_mode_desc = f"BIDIRECTIONAL CORRIDOR SEARCH (Optimal Upstream/Downstream: ±{max_gap_sec:.0f}s around {ref_dt.strftime('%H:%M:%S')})"
    else:
        t_min = None
        t_max = None
        time_filter_label = "ALL TIMES (EXTERNAL QUERY)"
        filter_mode_desc = "ALL TIMES (External image without sighting timestamp or window)"

    print("\n" + "=" * 90)
    print(" 🚗 MULTI-CAMERA VEHICLE RE-ID & TRAJECTORY TRACKING (BIDIRECTIONAL RESOLUTION)")
    print("=" * 90)
    print(f"  Query Image Path   : {query_img_path}")
    if query_key:
        print(f"  Identified Vehicle : {query_key}")
        print(f"  Origin Camera      : {query_cam}")
        print(f"  Plate in Origin    : {q_plate} "
              f"({query_meta.get('average_ocr_confidence', 0.0):.1f}% OCR confidence)")
        print(f"  Entry Window       : {query_meta.get('entry_timestamp', 'N/A')} -> "
              f"{query_meta.get('exit_timestamp', 'N/A')} (Duration: {q_dur:.1f}s)")
    elif ref_dt:
        print(f"  Reference Time     : {ref_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("  Query Type         : Custom External Image (Searching across network)")
    print(f"  Time Filter Mode   : {filter_mode_desc}")
    if t_min or t_max:
        w_min_s = t_min.strftime('%Y-%m-%d %H:%M:%S') if t_min else "Beginning of Feed"
        w_max_s = t_max.strftime('%Y-%m-%d %H:%M:%S') if t_max else "End of Feed"
        print(f"  Search Window      : {w_min_s} -> {w_max_s}")
    print("-" * 90)

    # 4. Search and Multi-Modal Scoring for Every Target Camera
    all_cams = sorted(camera_matrices.keys())
    target_cams = [c for c in all_cams if c != query_cam] if query_cam else all_cams

    camera_best = {}
    camera_top_candidates = {}
    all_target_cands = []

    for t_cam in target_cams:
        keys = camera_keys.get(t_cam, [])
        matrix = camera_matrices.get(t_cam, np.empty((0, len(q_emb))))
        if len(keys) == 0:
            continue

        # 4a. Temporal Pre-Filtering: restrict candidates to search window
        if t_min is not None or t_max is not None:
            valid_indices = []
            for idx, c_k in enumerate(keys):
                c_m = csv_metadata.get(c_k, {})
                c_ent = parse_timestamp(c_m.get("entry_timestamp", ""), default_date=base_date)
                c_ext = parse_timestamp(c_m.get("exit_timestamp", ""), default_date=base_date)
                cand_dt = c_ent or c_ext

                if cand_dt is not None:
                    if t_min is not None and cand_dt < t_min:
                        continue
                    if t_max is not None and cand_dt > t_max:
                        continue
                    valid_indices.append(idx)

            if not valid_indices:
                print(f"  ℹ️  [{t_cam}] 0 / {len(keys)} candidates fall within temporal window ({time_filter_label}). Skipping camera.")
                continue

            sub_keys = [keys[i] for i in valid_indices]
            sub_matrix = matrix[valid_indices]
        else:
            sub_keys = keys
            sub_matrix = matrix

        sims = np.dot(sub_matrix, q_emb)
        ranked = np.argsort(-sims)

        # Evaluate candidates with Multi-Modal Fusion (Re-ID + Color + Plate + Forward Transit)
        cand_list = []
        for r_idx in ranked[:30]:
            c_k = sub_keys[r_idx]
            c_s = float(sims[r_idx])
            c_m = csv_metadata.get(c_k, {})
            c_p = c_m.get("plate_number", "UNKNOWN").strip().upper()
            c_conf = float(c_m.get("average_ocr_confidence") or 0.0)
            c_entry_dt = parse_timestamp(c_m.get("entry_timestamp", ""), default_date=base_date)

            gap_sec = None
            if ref_dt and c_entry_dt:
                gap_sec = (c_entry_dt - ref_dt).total_seconds()
            elif query_entry_dt and c_entry_dt:
                gap_sec = (c_entry_dt - query_entry_dt).total_seconds()

            transit = format_transit_details(gap_sec, query_cam, t_cam)

            img_p = crop_images.get(c_k, "")
            img_data = cv2.imread(img_p) if img_p and os.path.exists(img_p) else None

            # Color Consistency Filter (HSV Histograms)
            c_sim = compute_color_similarity(query_img, img_data)

            composite = c_s
            plate_matched = False
            if q_plate != "UNKNOWN" and c_p != "UNKNOWN":
                p_ratio = difflib.SequenceMatcher(None, q_plate, c_p).ratio()
                if p_ratio >= 0.75:
                    composite += 0.35  # Major boost for plate match
                    plate_matched = True
                elif p_ratio >= 0.5:
                    composite += 0.12

            # Physical Color Invariance Gating:
            # If plates don't match, vehicle colors MUST be physically consistent across cameras!
            if not plate_matched:
                if c_sim < 0.55:
                    composite -= 0.35  # Heavy penalty for incompatible colors (e.g. blue vs white)
                elif c_sim >= 0.80:
                    composite += 0.08  # Consistency bonus

            # Plausible bidirectional transit bonus:
            # Vehicles travel both directions (incoming and outgoing). Adjacent corridor transit receives bonus.
            if gap_sec is not None and abs(gap_sec) <= 180.0:
                composite += 0.05
                # Strong proximity bonus for immediate corridor sightings within 60s
                if abs(gap_sec) <= 60.0:
                    composite += 0.05

            cand_list.append({
                "camera_id": t_cam,
                "key": c_k,
                "track_id": c_m.get("track_id", c_k.split("_track_")[-1]),
                "sim": c_s,
                "composite_score": composite,
                "plate_matched": plate_matched,
                "color_sim": c_sim,
                "meta": c_m,
                "plate": c_p,
                "ocr_conf": c_conf,
                "transit": transit,
                "transit_gap": gap_sec,
                "entry_dt": c_entry_dt,
                "entry_ts": c_m.get("entry_timestamp", "N/A"),
                "exit_ts": c_m.get("exit_timestamp", "N/A"),
                "crop_path": img_p,
                "img": img_data,
                "is_confirmed": False,
                "is_origin": False
            })

        cand_list.sort(key=lambda c: -c["composite_score"])
        if cand_list:
            camera_best[t_cam] = cand_list[0]
            camera_top_candidates[t_cam] = cand_list[:5]
            all_target_cands.extend(cand_list)

    all_target_cands.sort(key=lambda c: -c["composite_score"])
    top_overall_matches = all_target_cands[:top_n]

    # 5. Enforce 2-Camera Network Topology
    confirmed_match = None
    rejected_hop = None

    print(" 🧭 JUNCTION TOPOLOGY & BIDIRECTIONAL ROUTE RESOLUTION:")

    # Identify Stem/Root corridor and Branch A/B dynamically:
    # If network has Camera_4, Camera_5, Camera_6:
    #   Stem is Camera_4; Branches are Camera_5 and Camera_6
    # If network has Camera_1, Camera_2, Camera_3:
    #   Stem is Camera_1; Branches are Camera_2 and Camera_3
    stem_cam = "Camera_4" if "Camera_4" in all_cams else "Camera_1"
    branch_cams = ("Camera_5", "Camera_6") if stem_cam == "Camera_4" else ("Camera_2", "Camera_3")

    if query_cam == stem_cam:
        # Vehicle entered at stem corridor and must take either Branch A OR Branch B
        b1_cam, b2_cam = branch_cams
        c1_cand = camera_best.get(b1_cam)
        c2_cand = camera_best.get(b2_cam)

        print(f"   Evaluating Fork Branches ({b1_cam} vs {b2_cam}):")
        if c1_cand:
            p1 = c1_cand['plate']
            print(f"    • {b1_cam} candidate: {c1_cand['key']} | Sim: {c1_cand['sim']:.4f} | "
                  f"Color: {c1_cand['color_sim']*100:.1f}% | Score: {c1_cand['composite_score']:.4f} | "
                  f"Plate: {p1} | {c1_cand['transit']['label']}")
        if c2_cand:
            p2 = c2_cand['plate']
            print(f"    • {b2_cam} candidate: {c2_cand['key']} | Sim: {c2_cand['sim']:.4f} | "
                  f"Color: {c2_cand['color_sim']*100:.1f}% | Score: {c2_cand['composite_score']:.4f} | "
                  f"Plate: {p2} | {c2_cand['transit']['label']}")

        if c1_cand and c2_cand:
            if c1_cand["composite_score"] >= c2_cand["composite_score"]:
                confirmed_match = c1_cand
                rejected_hop = c2_cand
                if c1_cand.get("plate_matched"):
                    rej_reason = f"Plate Match Confirmed in {b1_cam} ({c1_cand['plate']} vs {q_plate})"
                else:
                    rej_reason = f"Lower Match Score ({c2_cand['composite_score']:.3f} vs {c1_cand['composite_score']:.3f})"
                rejected_hop["rejection_reason"] = f"{rej_reason} | Divergent Fork Rejected"
                print(f"   ► Decision: Vehicle took Branch {b1_cam}! Branch {b2_cam} REJECTED ({rej_reason}).")
            else:
                confirmed_match = c2_cand
                rejected_hop = c1_cand
                if c2_cand.get("plate_matched"):
                    rej_reason = f"Plate Match Confirmed in {b2_cam} ({c2_cand['plate']} vs {q_plate})"
                else:
                    rej_reason = f"Lower Match Score ({c1_cand['composite_score']:.3f} vs {c2_cand['composite_score']:.3f})"
                rejected_hop["rejection_reason"] = f"{rej_reason} | Divergent Fork Rejected"
                print(f"   ► Decision: Vehicle took Branch {b2_cam}! Branch {b1_cam} REJECTED ({rej_reason}).")
        elif c1_cand:
            confirmed_match = c1_cand
        elif c2_cand:
            confirmed_match = c2_cand

    elif query_cam in branch_cams:
        # Connected corridor is stem corridor. The other branch is disconnected/parallel.
        b1_cam, b2_cam = branch_cams
        other_branch = b2_cam if query_cam == b1_cam else b1_cam
        confirmed_match = camera_best.get(stem_cam)
        print(f"   Origin is {query_cam}. Connected road corridor is {stem_cam}.")
        if confirmed_match:
            print(f"    • Connected {stem_cam} sighting: {confirmed_match['key']} | Sim: {confirmed_match['sim']:.4f} | "
                  f"Color: {confirmed_match['color_sim']*100:.1f}% | Score: {confirmed_match['composite_score']:.4f} | "
                  f"{confirmed_match['transit']['label']}")
        if other_branch in camera_best:
            rejected_hop = camera_best[other_branch]
            rejected_hop["rejection_reason"] = (
                f"Disconnected Parallel Branch ({query_cam} <-> {other_branch} not connected directly)"
            )
            print(f"   ► Rejected Branch {other_branch}: Parallel divergent fork not directly connected.")

    else:
        # Unknown/External image: rank all cameras and take top candidate
        if top_overall_matches:
            confirmed_match = top_overall_matches[0]

    # 5b. Minimum Confidence Threshold Gating
    MIN_CONFIDENCE_THRESHOLD = 0.78
    if confirmed_match and not confirmed_match.get("plate_matched"):
        if confirmed_match["composite_score"] < MIN_CONFIDENCE_THRESHOLD:
            print(f"\n   ⚠️  Best candidate '{confirmed_match['key']}' scored {confirmed_match['composite_score']:.4f} "
                  f"(below confidence threshold {MIN_CONFIDENCE_THRESHOLD}).")
            print("   ► Decision: NO CONFIRMED DOWNSTREAM/UPSTREAM SIGHTING (Vehicle likely exited corridor or turned).")
            confirmed_match = None

    if confirmed_match:
        confirmed_match["is_confirmed"] = True
        for m in top_overall_matches:
            if m["key"] == confirmed_match["key"]:
                m["is_confirmed"] = True

    # 6. Assemble Confirmed Trajectory Hops & Chronological Sighting Ordering
    trajectory_hops = []
    if query_cam and query_key:
        trajectory_hops.append({
            "camera_id": query_cam,
            "track_id": query_meta.get("track_id", query_key.split("_track_")[-1]),
            "key": query_key,
            "sim": 1.0,
            "is_origin": True,
            "img": query_img,
            "meta": query_meta,
            "plate": q_plate,
            "ocr_conf": query_meta.get("average_ocr_confidence", 0.0),
            "transit_gap": 0.0,
            "entry_dt": query_entry_dt,
            "plate_matched": False
        })

    if confirmed_match:
        trajectory_hops.append(confirmed_match)

    if any(h.get("entry_dt") for h in trajectory_hops):
        trajectory_hops.sort(key=lambda h: (h.get("entry_dt") is None, h.get("entry_dt") or datetime.min))

    # 7. Format Reconstructed Route String
    route_parts = []
    for h in trajectory_hops:
        cid = h["camera_id"].replace("Camera_", "CAM")
        ts = h.get("entry_dt")
        ts_str = f" ({ts.strftime('%H:%M:%S')})" if ts else ""
        if h.get("is_origin"):
            route_parts.append(f"{cid}{ts_str} [QUERY]")
        else:
            dir_str = h.get("transit", {}).get("direction", "Match")
            route_parts.append(f"{cid}{ts_str} [{dir_str} {h['sim']:.3f}]")
    if len(trajectory_hops) == 1:
        route_parts.append("[NO NETWORK MATCH (<0.78)]")
    route_str = " ──► ".join(route_parts)

    print("-" * 90)
    print(f" 📍 CONFIRMED TRAJECTORY ROUTE:")
    print(f"    {route_str}")
    print("-" * 90)

    # 8. Print Match Results
    if top_n == 1:
        print(" 🏆 OPTIMAL CROSS-CAMERA VEHICLE MATCH:\n")
    else:
        print(f" 🏆 TOP {len(top_overall_matches)} MATCHED VEHICLES ACROSS CAMERAS (MULTI-MODAL RANKING):\n")

    for rank, m in enumerate(top_overall_matches, start=1):
        if top_n == 1:
            tag = "CONFIRMED MATCH" if m.get("is_confirmed") else "BEST CANDIDATE"
            print(f"  ► {tag}: {m['key']} (Composite Score: {m['composite_score']:.4f})")
        else:
            tag = "CONFIRMED MATCH" if m.get("is_confirmed") else ("TOP CANDIDATE" if rank == 1 else "CANDIDATE")
            print(f"  [RANK #{rank}] {m['key']} ──► {tag} (Composite Score: {m['composite_score']:.4f})")
        print(f"     • Camera & Track : {m['camera_id']} | Track ID #{m['track_id']}")
        print(f"     • Re-ID Cosine   : {m['sim']:.4f} (Deep Feature Cosine Similarity)")
        print(f"     • Color Match    : {m['color_sim']*100:.1f}% ({'Consistent Vehicle Palette' if m['color_sim']>=0.70 else 'Color Mismatch'})")
        if m['plate'] != 'UNKNOWN':
            match_badge = " [PLATE MATCH]" if m.get("plate_matched") else ""
            print(f"     • Plate Number   : {m['plate']} (OCR Conf: {m['ocr_conf']:.1f}%){match_badge}")
        else:
            print("     • Plate Number   : UNKNOWN")
        print(f"     • Direction & Gap: {m['transit']['label']}")
        print(f"     • Corridor Route : {m['transit']['route']}")
        print(f"     • Sighting Window: {m['entry_ts']} -> {m['exit_ts']}")
        e_off = float(m['meta'].get("entry_offset_sec") or 0.0)
        x_off = float(m['meta'].get("exit_offset_sec") or 0.0)
        print(f"     • Video Offsets  : {e_off:.2f}s -> {x_off:.2f}s in {m['camera_id']} feed (Duration: {x_off - e_off:.2f}s)")
        print(f"     • Evidence Crop  : {m['crop_path']}")
        print()

    # 9. Print Rejected Branch Information
    if rejected_hop:
        print("-" * 90)
        print(" 🚫 REJECTED DIVERGENT BRANCH CANDIDATE:")
        print(f"     • Camera        : {rejected_hop['camera_id']}")
        print(f"     • Track Key     : {rejected_hop['key']}")
        print(f"     • Plate         : {rejected_hop.get('plate', 'UNKNOWN')}")
        print(f"     • Re-ID Sim     : {rejected_hop['sim']:.4f}")
        print(f"     • Reason        : {rejected_hop.get('rejection_reason', 'Lower score')}")
        print(f"     • Topology Rule : Enforcing max 2 cameras per vehicle corridor")

    # 10. Print Top Candidates by Camera
    print("-" * 90)
    print(" 📋 TOP CANDIDATES BY CAMERA (FOR DETAILED FORENSIC VERIFICATION):")
    for t_cam, cands in camera_top_candidates.items():
        print(f"   [{t_cam}]")
        for rank, c_item in enumerate(cands, start=1):
            c_k = c_item["key"]
            c_s = c_item["sim"]
            c_comp = c_item["composite_score"]
            c_col = c_item["color_sim"] * 100.0
            c_p = c_item.get("plate", "UNKNOWN")
            c_lbl = c_item["transit"]["label"]
            print(f"     #{rank} | {c_k:<24} | Score: {c_comp:.3f} | Sim: {c_s:.4f} | Color: {c_col:5.1f}% | {c_lbl:<24} | Plate: {c_p}")
    print("=" * 90)

    # 11. Render Visual Multi-Camera Dashboard Canvas (Query + Top Matches)
    query_card_data = {
        "camera_id": query_cam or "External",
        "key": query_key or os.path.basename(query_img_path),
        "track_id": query_meta.get("track_id", query_key.split("_track_")[-1] if query_key else "N/A"),
        "plate": q_plate,
        "conf": query_meta.get("average_ocr_confidence", 0.0),
        "entry_ts": query_meta.get("entry_timestamp", "") or (ref_dt.strftime("%Y-%m-%d %H:%M:%S") if ref_dt else "N/A"),
        "exit_ts": query_meta.get("exit_timestamp", "") or (ref_dt.strftime("%Y-%m-%d %H:%M:%S") if ref_dt else "N/A"),
        "duration": q_dur,
        "img": query_img
    }

    save_path = custom_save_path or os.path.join(output_dir, "reid_trajectory_result.jpg")
    canvas = build_multi_match_canvas(
        query_card_data=query_card_data,
        matches=top_overall_matches,
        route_summary=route_str,
        save_path=save_path,
        rejected_hop=rejected_hop,
        time_filter_label=time_filter_label
    )

    # 12. Launch Pop-up Window
    display_popup(
        canvas=canvas,
        save_path=save_path,
        title=f"Cross-Camera Re-ID: {os.path.basename(query_img_path)}",
        no_popup=no_popup
    )


# =========================================================================
#  BENCHMARK WORKFLOW
# =========================================================================

def run_batch_benchmark(reid_model, queries: List[Tuple[str, str]], gallery_keys: List[str],
                        gallery_matrix: np.ndarray, top_k: int, batch_size: int, verbose: bool):
    """Run full benchmark evaluating all query sample crops in batches."""
    top1_correct = 0
    topk_correct = 0
    reciprocal_ranks = []
    true_match_sims = []
    hardest_false_sims = []

    per_vehicle_stats = defaultdict(lambda: {"total": 0, "top1": 0, "topk": 0})
    key_to_idx = {k: i for i, k in enumerate(gallery_keys)}

    total_queries = len(queries)
    batch_size = max(1, batch_size)
    print(f"\nEvaluating {total_queries} query crops against {len(gallery_keys)} gallery vehicles in batches of {batch_size}...\n")
    start_time = time.time()
    eval_count = 0

    for b_idx in range(0, total_queries, batch_size):
        batch_queries = queries[b_idx:b_idx + batch_size]
        batch_imgs = []
        batch_valid = []

        for q_gt_key, q_img_path in batch_queries:
            img = cv2.imread(q_img_path)
            if img is not None and img.size > 0:
                batch_imgs.append(img)
                batch_valid.append((q_gt_key, q_img_path))

        if not batch_imgs:
            continue

        if hasattr(reid_model, "get_batch_embeddings"):
            batch_embs = reid_model.get_batch_embeddings(batch_imgs, batch_size=batch_size)
        else:
            batch_embs = np.array([reid_model.get_embedding(im) for im in batch_imgs], dtype=np.float32)

        batch_sims = np.matmul(batch_embs, gallery_matrix.T)

        for i, (gt_key, img_path) in enumerate(batch_valid):
            eval_count += 1
            sims = batch_sims[i]
            ranked_indices = np.argsort(-sims)
            gt_idx = key_to_idx[gt_key]
            rank = int(np.where(ranked_indices == gt_idx)[0][0]) + 1

            is_top1 = (rank == 1)
            is_topk = (rank <= top_k)

            top1_correct += int(is_top1)
            topk_correct += int(is_topk)
            reciprocal_ranks.append(1.0 / rank)

            true_sim = float(sims[gt_idx])
            true_match_sims.append(true_sim)

            if len(sims) > 1:
                hardest_false_idx = ranked_indices[0] if ranked_indices[0] != gt_idx else ranked_indices[1]
                hardest_false_sims.append(float(sims[hardest_false_idx]))

            per_vehicle_stats[gt_key]["total"] += 1
            per_vehicle_stats[gt_key]["top1"] += int(is_top1)
            per_vehicle_stats[gt_key]["topk"] += int(is_topk)

            if verbose:
                status = "✅ PASS (Rank 1)" if is_top1 else (f"🟡 TOP-{top_k} (Rank {rank})" if is_topk else f"❌ FAIL (Rank {rank})")
                top_match_key = gallery_keys[ranked_indices[0]]
                print(f"  [{eval_count:04d}/{total_queries:04d}] {gt_key:<26} -> {status:<18} | Top Match: {top_match_key} ({sims[ranked_indices[0]]:.3f})")

        if not verbose and (eval_count % 128 == 0 or eval_count == total_queries):
            cur_top1 = (top1_correct / eval_count) * 100.0
            cur_topk = (topk_correct / eval_count) * 100.0
            cur_mrr = float(np.mean(reciprocal_ranks))
            pct = (eval_count / total_queries) * 100.0
            elapsed_cur = time.time() - start_time
            rate = eval_count / max(elapsed_cur, 0.001)
            print(f"  Progress: [{eval_count:4d}/{total_queries:4d}] ({pct:5.1f}%) | Top-1: {cur_top1:5.1f}% | Top-{top_k}: {cur_topk:5.1f}% | MRR: {cur_mrr:.3f} | {rate:.1f} q/s", flush=True)

    elapsed = time.time() - start_time
    total_eval = len(reciprocal_ranks)

    if total_eval == 0:
        print("[ERROR] No queries could be evaluated.")
        sys.exit(1)

    top1_acc = (top1_correct / total_eval) * 100.0
    topk_acc = (topk_correct / total_eval) * 100.0
    mrr = float(np.mean(reciprocal_ranks))

    avg_true_sim = float(np.mean(true_match_sims)) if true_match_sims else 0.0
    avg_false_sim = float(np.mean(hardest_false_sims)) if hardest_false_sims else 0.0
    margin = avg_true_sim - avg_false_sim

    print("\n" + "=" * 75)
    print(" 📊 RE-ID RETRIEVAL ACCURACY REPORT")
    print("=" * 75)
    print(f"  Total Gallery Vehicles Tested : {len(gallery_keys):,}")
    print(f"  Total Query Samples Evaluated : {total_eval:,}")
    print(f"  Evaluation Time               : {elapsed:.2f}s ({total_eval / max(elapsed, 0.001):.1f} queries/sec)")
    print("-" * 75)
    print(f"  🏆 Top-1 Accuracy             : {top1_acc:6.2f}%  ({top1_correct}/{total_eval})")
    print(f"  🎯 Top-{top_k} Accuracy             : {topk_acc:6.2f}%  ({topk_correct}/{total_eval})")
    print(f"  📈 Mean Reciprocal Rank (MRR) : {mrr:6.4f}")
    print("-" * 75)
    print(f"  🔹 Avg True Match Cosine Sim  : {avg_true_sim:.4f}")
    print(f"  🔸 Avg Hardest False Cosine Sim: {avg_false_sim:.4f}")
    print(f"  ✨ Separation Margin (Δ)      : {margin:+.4f}")
    print("=" * 75 + "\n")


# =========================================================================
#  MAIN ENTRY POINT
# =========================================================================

def main():
    args = parse_args()

    base_dir, crops_dir, samples_dir, csv_path = resolve_output_dirs(
        args.output_dir, args.crops_dir, args.samples_dir, args.csv_path
    )

    print("\n" + "=" * 75)
    print(" 🚗 VEHICLE RE-ID EMBEDDING RETRIEVAL & TRAJECTORY TRACKING")
    print("=" * 75)
    print(f"  Gallery Directory : {crops_dir}")
    print(f"  CSV Telemetry     : {csv_path}")
    print(f"  Model             : {args.model.upper()}")
    print("=" * 75)

    # 1. Load Gallery partitioned by camera
    camera_keys, camera_matrices, crop_images = load_gallery_by_camera(crops_dir)
    total_gallery = sum(len(k) for k in camera_keys.values())

    if total_gallery == 0:
        print(f"\n[ERROR] No gallery embeddings (*_emb.npy) found in: {crops_dir}")
        print("Please check that the output directory has been generated by 'python pipeline/main.py'.\n")
        sys.exit(1)

    print(f"✅ Loaded {total_gallery} vehicle embeddings across {len(camera_keys)} cameras:")
    for cam, keys in sorted(camera_keys.items()):
        print(f"   • {cam}: {len(keys)} embeddings")

    # 2. Load CSV Metadata
    csv_metadata = load_csv_metadata(csv_path)
    if csv_metadata:
        print(f"✅ Loaded {len(csv_metadata)} vehicle telemetry records from CSV.")
    else:
        print(f"⚠️  CSV telemetry not found at '{csv_path}'. Continuing without CSV metadata.")

    # 3. Load Re-ID Model
    device = args.device if args.device else None
    print(f"⚙️  Loading Re-ID Feature Extractor [{args.model}]...")
    reid_model = get_reid_model(args.model, device=device)

    # ---------------------------------------------------------------------
    # Case A: Track Specific Vehicle by Key (--track <Camera_4_track_190>)
    # ---------------------------------------------------------------------
    if args.track:
        query_img_path = crop_images.get(args.track, "")
        if not query_img_path or not os.path.exists(query_img_path):
            # Try finding it in crops_dir
            candidate = os.path.join(crops_dir, f"{args.track}.jpg")
            if os.path.exists(candidate):
                query_img_path = candidate
            else:
                print(f"[ERROR] Crop image for track '{args.track}' not found.")
                sys.exit(1)

        track_cross_camera_trajectory(
            reid_model=reid_model,
            query_img_path=query_img_path,
            camera_keys=camera_keys,
            camera_matrices=camera_matrices,
            crop_images=crop_images,
            csv_metadata=csv_metadata,
            output_dir=base_dir,
            no_popup=args.no_popup,
            custom_save_path=args.save_path,
            top_n=args.top_n,
            query_time=args.time,
            time_range=args.time_range,
            start_time=args.start_time,
            end_time=args.end_time,
            forward_only=args.forward_only,
            max_gap_sec=args.max_gap,
            tolerance_sec=args.tolerance,
            all_times=args.all_times
        )
        return

    # ---------------------------------------------------------------------
    # Case B: Cross-Camera Search by Image Path (--image <path>)
    # ---------------------------------------------------------------------
    if args.image:
        track_cross_camera_trajectory(
            reid_model=reid_model,
            query_img_path=args.image,
            camera_keys=camera_keys,
            camera_matrices=camera_matrices,
            crop_images=crop_images,
            csv_metadata=csv_metadata,
            output_dir=base_dir,
            no_popup=args.no_popup,
            custom_save_path=args.save_path,
            top_n=args.top_n,
            query_time=args.time,
            time_range=args.time_range,
            start_time=args.start_time,
            end_time=args.end_time,
            forward_only=args.forward_only,
            max_gap_sec=args.max_gap,
            tolerance_sec=args.tolerance,
            all_times=args.all_times
        )
        return

    # ---------------------------------------------------------------------
    # Case C: Pick One Random Vehicle (--one [--camera <Camera_4>])
    # ---------------------------------------------------------------------
    if args.one:
        # Determine pool of candidates
        cands = []
        if args.camera and args.camera in camera_keys:
            cands = [crop_images[k] for k in camera_keys[args.camera] if crop_images.get(k)]
        else:
            # Pick from any camera that has sample crops or crops
            for cam, keys in camera_keys.items():
                cands.extend([crop_images[k] for k in keys if crop_images.get(k)])

        if not cands:
            print(f"[ERROR] No valid vehicle crop images found for query.")
            sys.exit(1)

        query_img_path = random.choice(cands)
        print(f"\n🎲 Selected Query Crop: {query_img_path}")

        track_cross_camera_trajectory(
            reid_model=reid_model,
            query_img_path=query_img_path,
            camera_keys=camera_keys,
            camera_matrices=camera_matrices,
            crop_images=crop_images,
            csv_metadata=csv_metadata,
            output_dir=base_dir,
            no_popup=args.no_popup,
            custom_save_path=args.save_path,
            top_n=args.top_n,
            query_time=args.time,
            time_range=args.time_range,
            start_time=args.start_time,
            end_time=args.end_time,
            forward_only=args.forward_only,
            max_gap_sec=args.max_gap,
            tolerance_sec=args.tolerance,
            all_times=args.all_times
        )
        return

    # ---------------------------------------------------------------------
    # Case D: Full Benchmark (Default)
    # ---------------------------------------------------------------------
    # Flatten gallery for benchmark
    flat_keys = []
    flat_matrix = []
    for cam in sorted(camera_keys.keys()):
        flat_keys.extend(camera_keys[cam])
        flat_matrix.append(camera_matrices[cam])

    dim = flat_matrix[0].shape[1] if (flat_matrix and len(flat_matrix[0]) > 0) else 512
    all_gallery_matrix = np.vstack(flat_matrix) if flat_matrix else np.empty((0, dim))

    # Discover sample queries
    valid_keys_set = set(flat_keys)
    queries = []
    if os.path.isdir(samples_dir):
        for entry in os.scandir(samples_dir):
            if entry.is_dir() and entry.name in valid_keys_set:
                for img_file in glob.glob(os.path.join(entry.path, "*.jpg")):
                    queries.append((entry.name, img_file))

    if not queries:
        print(f"\n[ERROR] No matching sample queries found in: {samples_dir}")
        print("Run with '--one' or '--image <path>' to track a vehicle across cameras.")
        sys.exit(1)

    print(f"✅ Found {len(queries)} query sample crops across {len(set(k for k, _ in queries))} vehicles.")

    run_batch_benchmark(
        reid_model=reid_model,
        queries=queries,
        gallery_keys=flat_keys,
        gallery_matrix=all_gallery_matrix,
        top_k=args.top_k,
        batch_size=args.batch_size,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
