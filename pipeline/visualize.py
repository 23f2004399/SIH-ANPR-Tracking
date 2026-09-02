#!/usr/bin/env python3
"""
Vehicle & License Plate Visualizer / Inspector
================================================================================
SIH Problem Statement: 26127 (Bharat Electronics Limited)

Usage:
  python visualize.py 1
  python visualize.py 1 --output_dir ./outputs
  python visualize.py 1 --camera Camera_1
"""

import os
import sys
import glob
import csv
import argparse
from typing import Optional, Dict, Tuple

import cv2
import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(
        description="Inspect vehicle crop, license plate crop, and OCR metadata for a specific Track ID"
    )
    parser.add_argument(
        "track_id",
        type=int,
        nargs="?",
        default=None,
        help="The numeric Track ID to inspect (e.g. 1, 2, 45)"
    )
    parser.add_argument(
        "--track_id",
        dest="flag_track_id",
        type=int,
        default=None,
        help="Optional flag format for Track ID"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./outputs",
        help="Directory containing outputs, crops, and vehicle_logs.csv (default: ./outputs)"
    )
    parser.add_argument(
        "--camera",
        type=str,
        default="",
        help="Optional camera filter (e.g. Camera_1)"
    )
    parser.add_argument(
        "--save_preview",
        type=str,
        default="",
        help="Path to save inspection composite image (defaults to outputs/inspect_track_<ID>.jpg)"
    )
    return parser.parse_args()


def load_track_metadata(csv_path: str, target_track_id: int, camera_filter: str = "") -> Optional[Dict[str, str]]:
    """Look up record in vehicle_logs.csv."""
    if not os.path.exists(csv_path):
        return None

    matched_row = None
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row_track_id = int(row.get("track_id", -1))
                row_cam = row.get("camera_id", "")
                if row_track_id == target_track_id:
                    if not camera_filter or camera_filter.lower() in row_cam.lower():
                        matched_row = row
                        break
            except ValueError:
                continue

    return matched_row


def list_available_tracks(crops_dir: str, csv_path: str):
    """List available track IDs to help user if ID is not found."""
    found_ids = set()
    
    # Check vehicle crops
    v_files = glob.glob(os.path.join(crops_dir, "vehicles", "*_track_*.jpg"))
    for vf in v_files:
        try:
            tid = int(os.path.splitext(vf)[0].split("_track_")[-1])
            found_ids.add(tid)
        except Exception:
            pass

    # Check CSV
    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    found_ids.add(int(row.get("track_id", -1)))
                except ValueError:
                    pass

    return sorted(list(found_ids))


def create_inspection_dashboard(
    track_id: int,
    camera_id: str,
    meta: Optional[Dict[str, str]],
    v_img: Optional[np.ndarray],
    p_img: Optional[np.ndarray]
) -> np.ndarray:
    """
    Generate a high-resolution, futuristic inspection canvas combining vehicle crop and plate crop.
    """
    canvas_w = 960
    canvas_h = 560
    canvas = np.full((canvas_h, canvas_w, 3), (20, 24, 30), dtype=np.uint8)

    # 1. Header Bar
    cv2.rectangle(canvas, (0, 0), (canvas_w, 70), (28, 34, 44), -1)
    cv2.line(canvas, (0, 70), (canvas_w, 70), (45, 55, 72), 2)

    cv2.putText(canvas, f"VEHICLE INSPECTION REPORT | TRACK #{track_id}", (30, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 215, 255), 2, cv2.LINE_AA)
    cv2.putText(canvas, f"NODE: {camera_id.upper()}", (canvas_w - 240, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (160, 175, 200), 2, cv2.LINE_AA)

    # 2. Vehicle Crop Display (Left Panel)
    left_x1, left_y1, left_w, left_h = 30, 95, 480, 420
    cv2.rectangle(canvas, (left_x1, left_y1), (left_x1 + left_w, left_y1 + left_h), (30, 36, 48), -1)
    cv2.rectangle(canvas, (left_x1, left_y1), (left_x1 + left_w, left_y1 + left_h), (50, 60, 80), 1)

    cv2.putText(canvas, "VEHICLE CROP", (left_x1 + 15, left_y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 210, 225), 1, cv2.LINE_AA)

    if v_img is not None and v_img.size > 0:
        # Resize preserving aspect ratio inside inner box
        box_w, box_h = left_w - 30, left_h - 60
        vh, vw = v_img.shape[:2]
        scale = min(box_w / vw, box_h / vh)
        nw, nh = max(1, int(vw * scale)), max(1, int(vh * scale))
        resized_v = cv2.resize(v_img, (nw, nh), interpolation=cv2.INTER_AREA)

        ox = left_x1 + 15 + (box_w - nw) // 2
        oy = left_y1 + 45 + (box_h - nh) // 2
        canvas[oy:oy + nh, ox:ox + nw] = resized_v
        cv2.rectangle(canvas, (ox, oy), (ox + nw, oy + nh), (0, 165, 255), 2)
    else:
        cv2.putText(canvas, "No Vehicle Crop Found", (left_x1 + 120, left_y1 + 220), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 110, 130), 1)

    # 3. License Plate & Metadata Panel (Right Panel)
    right_x1, right_y1, right_w, right_h = 530, 95, 400, 420
    cv2.rectangle(canvas, (right_x1, right_y1), (right_x1 + right_w, right_y1 + right_h), (30, 36, 48), -1)
    cv2.rectangle(canvas, (right_x1, right_y1), (right_x1 + right_w, right_y1 + right_h), (50, 60, 80), 1)

    cv2.putText(canvas, "LICENSE PLATE LOCALIZATION", (right_x1 + 15, right_y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 210, 225), 1, cv2.LINE_AA)

    # Plate Crop Box
    pbox_x, pbox_y, pbox_w, pbox_h = right_x1 + 15, right_y1 + 45, right_w - 30, 130
    cv2.rectangle(canvas, (pbox_x, pbox_y), (pbox_x + pbox_w, pbox_y + pbox_h), (18, 22, 28), -1)

    if p_img is not None and p_img.size > 0:
        ph, pw = p_img.shape[:2]
        scale = min((pbox_w - 20) / pw, (pbox_h - 20) / ph)
        pnw, pnh = max(1, int(pw * scale)), max(1, int(ph * scale))
        resized_p = cv2.resize(p_img, (pnw, pnh), interpolation=cv2.INTER_NEAREST)

        pox = pbox_x + (pbox_w - pnw) // 2
        poy = pbox_y + (pbox_h - pnh) // 2
        canvas[poy:poy + pnh, pox:pox + pnw] = resized_p
        cv2.rectangle(canvas, (pox, poy), (pox + pnw, poy + pnh), (0, 255, 255), 2)
    else:
        cv2.putText(canvas, "NO PLATE CROP DETECTED", (pbox_x + 50, pbox_y + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (120, 130, 150), 1)
        cv2.rectangle(canvas, (pbox_x, pbox_y), (pbox_x + pbox_w, pbox_y + pbox_h), (60, 70, 85), 1)

    # Metadata Details
    plate_text = meta.get("plate_number", "UNKNOWN") if meta else "UNKNOWN"
    conf_str = f"{float(meta.get('average_ocr_confidence', 0)):.1f}%" if meta else "0.0%"
    entry_ts = meta.get("entry_timestamp", "N/A") if meta else "N/A"
    exit_ts = meta.get("exit_timestamp", "N/A") if meta else "N/A"

    info_y = right_y1 + 205
    cv2.putText(canvas, "RECOGNIZED NUMBER PLATE:", (right_x1 + 15, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 155, 175), 1, cv2.LINE_AA)

    # Large Plate String Display Pill
    plate_pill_color = (0, 180, 0) if plate_text != "UNKNOWN" else (50, 60, 75)
    cv2.rectangle(canvas, (right_x1 + 15, info_y + 12), (right_x1 + right_w - 15, info_y + 65), plate_pill_color, -1)
    cv2.rectangle(canvas, (right_x1 + 15, info_y + 12), (right_x1 + right_w - 15, info_y + 65), (255, 255, 255), 1)

    cv2.putText(
        canvas,
        plate_text,
        (right_x1 + 30, info_y + 50),
        cv2.FONT_HERSHEY_DUPLEX,
        1.1,
        (255, 255, 255) if plate_text != "UNKNOWN" else (180, 190, 200),
        2,
        cv2.LINE_AA
    )

    # Metadata Key-Value List
    rows = [
        ("OCR Confidence:", conf_str, (0, 220, 100) if float(conf_str.replace('%','')) > 0 else (160, 170, 180)),
        ("First Seen (Entry):", entry_ts, (220, 220, 220)),
        ("Last Seen (Exit):", exit_ts, (220, 220, 220)),
        ("Camera Feed:", camera_id, (0, 200, 255))
    ]

    base_y = info_y + 95
    for label, val, val_color in rows:
        cv2.putText(canvas, label, (right_x1 + 15, base_y), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (150, 165, 185), 1, cv2.LINE_AA)
        cv2.putText(canvas, val, (right_x1 + 190, base_y), cv2.FONT_HERSHEY_SIMPLEX, 0.48, val_color, 1, cv2.LINE_AA)
        base_y += 26

    # Bottom Instructions
    cv2.putText(canvas, "Press any key or 'Q' to exit inspection window", (30, canvas_h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (100, 115, 135), 1, cv2.LINE_AA)

    return canvas


def main():
    args = parse_args()
    target_id = args.track_id if args.track_id is not None else args.flag_track_id

    crops_dir = os.path.join(args.output_dir, "crops")
    csv_path = os.path.join(args.output_dir, "vehicle_logs.csv")

    if target_id is None:
        avail_ids = list_available_tracks(crops_dir, csv_path)
        print("\n" + "="*60)
        print(" [!] Please provide a Track ID to inspect.")
        print(f" Usage: python visualize.py <TRACK_ID>")
        print(f" Example: python visualize.py 1")
        if avail_ids:
            print(f" Currently available Track IDs: {avail_ids[:25]} ... (Total: {len(avail_ids)})")
        else:
            print(" No tracked vehicles found yet in outputs. Run 'python main.py' first.")
        print("="*60 + "\n")
        sys.exit(1)

    # Search for vehicle and plate crops
    v_matches = glob.glob(os.path.join(crops_dir, "vehicles", f"*_track_{target_id}.jpg"))
    p_matches = glob.glob(os.path.join(crops_dir, "plates", f"*_track_{target_id}.jpg"))

    if args.camera:
        v_matches = [f for f in v_matches if args.camera.lower() in os.path.basename(f).lower()]
        p_matches = [f for f in p_matches if args.camera.lower() in os.path.basename(f).lower()]

    v_path = v_matches[0] if v_matches else None
    p_path = p_matches[0] if p_matches else None

    # Load images
    v_img = cv2.imread(v_path) if (v_path and os.path.exists(v_path)) else None
    p_img = cv2.imread(p_path) if (p_path and os.path.exists(p_path)) else None

    # Load CSV metadata
    meta = load_track_metadata(csv_path, target_id, args.camera)

    camera_id = meta.get("camera_id", "Camera_1") if meta else (
        os.path.basename(v_path).split("_track_")[0] if v_path else "Camera_1"
    )

    if v_img is None and p_img is None and meta is None:
        avail_ids = list_available_tracks(crops_dir, csv_path)
        print(f"\n[ERROR] Track ID #{target_id} not found in '{args.output_dir}'!")
        if avail_ids:
            print(f"Available Track IDs in records: {avail_ids}\n")
        else:
            print("No tracks logged yet. Please execute main.py first.\n")
        sys.exit(1)

    # Print Terminal Telemetry Card
    plate_str = meta.get("plate_number", "UNKNOWN") if meta else "UNKNOWN"
    conf_str = f"{float(meta.get('average_ocr_confidence', 0)):.1f}%" if meta else "0.0%"
    entry_ts = meta.get("entry_timestamp", "N/A") if meta else "N/A"
    exit_ts = meta.get("exit_timestamp", "N/A") if meta else "N/A"

    print("\n" + "="*65)
    print(f" 🔎 VEHICLE INSPECTION DOSSIER : TRACK #{target_id}")
    print("="*65)
    print(f"  • Camera Node       : {camera_id}")
    print(f"  • Plate Recognized  : {plate_str}")
    print(f"  • OCR Confidence    : {conf_str}")
    print(f"  • Entry Timestamp   : {entry_ts}")
    print(f"  • Exit Timestamp    : {exit_ts}")
    print(f"  • Vehicle Crop Path : {v_path if v_path else 'None'}")
    print(f"  • Plate Crop Path   : {p_path if p_path else 'None'}")
    print("="*65)

    # Render Dashboard
    dashboard = create_inspection_dashboard(target_id, camera_id, meta, v_img, p_img)

    # Save preview image
    save_path = args.save_preview or os.path.join(args.output_dir, f"inspect_track_{target_id}.jpg")
    cv2.imwrite(save_path, dashboard)
    print(f" [✓] Inspection preview saved to: {save_path}\n")

    # Display Window if GUI environment supports it
    try:
        window_title = f"ZYRODEV Vehicle Inspector - Track #{target_id}"
        cv2.imshow(window_title, dashboard)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception as e:
        print(f" Note: GUI display skipped ({e}). Image saved to '{save_path}'.")


if __name__ == "__main__":
    main()
