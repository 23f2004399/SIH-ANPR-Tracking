#!/usr/bin/env python3
"""
Push vehicle_logs.csv into Supabase
====================================
Run supabase_schema.sql first, then this.

    export SUPABASE_URL=https://<project>.supabase.co
    export SUPABASE_SERVICE_KEY=sb_secret_...        # server-side only, never in frontend
    python upload_to_supabase.py

    python upload_to_supabase.py --video_base https://pub-xxxx.r2.dev
    python upload_to_supabase.py --dry_run          # print what would be sent

The secret key is read from the environment on purpose — it bypasses RLS, so it
must never end up in a file that could be committed or shipped to a browser.
"""

import os
import csv
import json
import argparse
import urllib.request
import urllib.error
from datetime import datetime

CSV_TS_FMT = "%Y-%m-%d %H:%M:%S.%f"
IST_OFFSET = "+05:30"          # footage timestamps are naive local (India) time
BATCH = 500

# The three prototype nodes, surveyed on site (DMS converted to decimal):
#   cam1  12°59'07.52"N  80°14'26.24"E
#   cam2  12°59'03.68"N  80°14'24.87"E
#   cam3  12°59'04.47"N  80°14'23.43"E
# cam2/cam3 sit ~50 m apart at the junction; cam1 is ~126 m up the road.
CAMERAS = [
    {"id": "Camera_1", "name": "OMR Junction North", "city": "Chennai",
     "latitude": 12.9854222, "longitude": 80.2406222, "file": "cam1.mp4"},
    {"id": "Camera_2", "name": "OMR Mid Corridor", "city": "Chennai",
     "latitude": 12.9843556, "longitude": 80.2402417, "file": "cam2.mp4"},
    {"id": "Camera_3", "name": "OMR Junction South", "city": "Chennai",
     "latitude": 12.9845750, "longitude": 80.2398417, "file": "cam3.mp4"},
]


def to_iso(value: str) -> str:
    """'2026-08-31 15:58:27.230' -> '2026-08-31T15:58:27.230+05:30'."""
    return datetime.strptime(value, CSV_TS_FMT).isoformat() + IST_OFFSET


def post(url: str, key: str, table: str, rows: list, upsert: bool = False):
    body = json.dumps(rows).encode()
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal" if upsert else "return=minimal",
    }
    req = urllib.request.Request(f"{url}/rest/v1/{table}", data=body,
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:400]
        raise SystemExit(f"\n[ERROR] {table} insert failed ({exc.code}): {detail}\n")


def load_detections(path: str):
    rows, skipped = [], 0
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                rows.append({
                    "camera_id":        r["camera_id"],
                    "track_id":         int(r["track_id"]),
                    "plate_number":     (r["plate_number"] or "UNKNOWN").strip().upper(),
                    "confidence":       float(r["average_ocr_confidence"] or 0),
                    "entry_timestamp":  to_iso(r["entry_timestamp"]),
                    "exit_timestamp":   to_iso(r["exit_timestamp"]),
                    "entry_offset_sec": float(r["entry_offset_sec"]),
                    "exit_offset_sec":  float(r["exit_offset_sec"]),
                })
            except (KeyError, ValueError):
                skipped += 1
    return rows, skipped


def main():
    ap = argparse.ArgumentParser(description="Upload vehicle_logs.csv to Supabase")
    ap.add_argument("csv_path", nargs="?", default="./outputs/vehicle_logs.csv")
    ap.add_argument("--video_base", default="",
                    help="Public base URL for the videos, e.g. https://pub-xxx.r2.dev "
                         "(leave blank to serve them locally from ./web_videos)")
    ap.add_argument("--recorded_at", default="2026-08-31 15:58:00",
                    help="Wall-clock start of the footage (must match main.py)")
    ap.add_argument("--dry_run", action="store_true")
    args = ap.parse_args()

    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not args.dry_run and not (url and key):
        raise SystemExit(
            "[ERROR] Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.\n"
            "        export SUPABASE_URL=https://<project>.supabase.co\n"
            "        export SUPABASE_SERVICE_KEY=sb_secret_...")

    base = args.video_base.rstrip("/") or "./web_videos"
    recorded = datetime.strptime(args.recorded_at, "%Y-%m-%d %H:%M:%S").isoformat() + IST_OFFSET
    cameras = [{
        "id": c["id"], "name": c["name"], "city": c["city"],
        "latitude": c["latitude"], "longitude": c["longitude"],
        "video_url": f"{base}/{c['file']}", "recorded_at": recorded,
    } for c in CAMERAS]

    detections, skipped = load_detections(args.csv_path)
    named = sum(1 for d in detections if d["plate_number"] != "UNKNOWN")

    print(f"\n  CSV        : {args.csv_path}")
    print(f"  cameras    : {len(cameras)}")
    print(f"  detections : {len(detections)}  ({named} with a plate, "
          f"{len(detections) - named} UNKNOWN kept for vehicle counts)")
    if skipped:
        print(f"  skipped    : {skipped} malformed row(s)")
    print(f"  video base : {base}")

    if args.dry_run:
        print("\n--- dry run, nothing sent ---")
        print(json.dumps(cameras[0], indent=2))
        print(json.dumps(detections[0], indent=2) if detections else "(no detections)")
        return

    print(f"\n  -> uploading cameras...", end=" ", flush=True)
    post(url, key, "cameras", cameras, upsert=True)
    print("ok")

    for i in range(0, len(detections), BATCH):
        chunk = detections[i:i + BATCH]
        post(url, key, "detections", chunk)
        print(f"  -> detections {i + len(chunk)}/{len(detections)}", end="\r", flush=True)

    print(f"\n\n  Done. {len(detections)} detection(s) uploaded.\n")


if __name__ == "__main__":
    main()
