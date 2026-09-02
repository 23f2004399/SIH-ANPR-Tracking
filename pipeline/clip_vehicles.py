#!/usr/bin/env python3
"""
Cut per-vehicle clips for the demo
===================================
For every confirmed cross-camera trajectory, cut the exact seconds each vehicle
was in each camera's frame out of the annotated videos.

The trajectories are regenerated with trajectory.py's own matching code rather
than parsed out of valid_track.txt — same 14 vehicles, but with millisecond
timestamps instead of the report's whole seconds, which matters when a sighting
is only two seconds long.

    python clip_vehicles.py                 # web_videos/ -> clips/
    python clip_vehicles.py --pad 2.5       # more lead-in / lead-out
    python clip_vehicles.py --src outputs --pattern 'annotated_CAM{n}_comp.mp4'
    python clip_vehicles.py --dry_run

Writes clips/manifest.json, which maps each plate to its ordered clips so the
dashboard can play them back without touching the full-length videos.
"""

import os
import json
import shutil
import argparse
import subprocess
from datetime import datetime

from trajectory import load_sightings, find_matches, build_trajectories

RECORDED_AT_FMT = "%Y-%m-%d %H:%M:%S"


def run_ffmpeg(src, dst, start, duration, crf, dry_run):
    """Re-encode the slice: -c copy would snap to the nearest keyframe and
    drift by up to several seconds, which is fatal for a 2-second sighting."""
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", f"{start:.3f}", "-i", src, "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-crf", str(crf), "-preset", "veryfast",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", dst,
    ]
    if dry_run:
        print("      " + " ".join(cmd))
        return True
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"      [ffmpeg error] {result.stderr.strip()[:200]}")
        return False
    return True


def probe_duration(path):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path],
            capture_output=True, text=True, check=True)
        return float(out.stdout.strip())
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description="Cut per-vehicle demo clips")
    ap.add_argument("log", nargs="?", default="./outputs/vehicle_logs.csv")
    ap.add_argument("--src", default="./web_videos",
                    help="Folder holding the annotated videos (default: ./web_videos)")
    ap.add_argument("--pattern", default="cam{n}.mp4",
                    help="Filename pattern, {n} = camera number (default: cam{n}.mp4)")
    ap.add_argument("--out", default="./clips",
                    help="Where the .mp4 clips are written")
    ap.add_argument("--manifest", default="./web/manifest.json",
                    help="Where the clip index is written (read by the dashboard)")
    ap.add_argument("--recorded_at", default="2026-08-31 15:58:00",
                    help="Wall-clock start of the footage — must match main.py")
    ap.add_argument("--pad", type=float, default=1.5,
                    help="Seconds of lead-in/out around each sighting (default: 1.5)")
    ap.add_argument("--crf", type=int, default=23, help="Quality, lower is better")
    ap.add_argument("--threshold", type=float, default=0.80,
                    help="Must match trajectory.py / index.html (default 0.80)")
    ap.add_argument("--min_len", type=int, default=8)
    ap.add_argument("--dry_run", action="store_true")
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        raise SystemExit("[ERROR] ffmpeg not found on PATH.")

    recorded_at = datetime.strptime(args.recorded_at, RECORDED_AT_FMT)

    sightings, _, _ = load_sightings(args.log, args.min_len, 0.0)
    matches = find_matches(sightings, args.threshold, 0.0)
    trajectories = build_trajectories(matches)
    if not trajectories:
        raise SystemExit("[ERROR] No cross-camera trajectories found.")

    os.makedirs(args.out, exist_ok=True)

    # Cache each source video's length so clips can be clamped to it.
    durations = {}
    print(f"\n{'='*80}")
    print(f"  Cutting clips for {len(trajectories)} vehicle(s)   pad={args.pad}s   -> {args.out}/")
    print(f"{'='*80}")

    manifest, made, failed = {}, 0, 0
    for plate, visits in trajectories:
        route = " -> ".join(v["camera"].replace("Camera_", "CAM") for v in visits)
        print(f"\n  ● {plate}   {route}")

        entries = []
        for visit in visits:
            cam = visit["camera"]
            n = cam.split("_")[-1]
            src = os.path.join(args.src, args.pattern.format(n=n))
            if not os.path.isfile(src):
                print(f"      [skip] source not found: {src}")
                failed += 1
                continue

            if src not in durations:
                durations[src] = probe_duration(src)
            total = durations[src]

            # Video offsets are just wall-clock minus the recording start, which
            # is how main.py built the timestamps in the first place.
            start_raw = (visit["first_seen"] - recorded_at).total_seconds()
            end_raw = (visit["last_seen"] - recorded_at).total_seconds()
            start = max(0.0, start_raw - args.pad)
            end = end_raw + args.pad
            if total:
                end = min(end, total)
            duration = end - start
            if duration <= 0.2:
                print(f"      [skip] {cam}: empty window")
                failed += 1
                continue

            name = f"{plate}_{cam}.mp4"
            dst = os.path.join(args.out, name)
            best_read, best_conf = visit["reads"][0]

            print(f"      {cam}  {start:7.2f}s -> {end:7.2f}s  ({duration:5.2f}s)  "
                  f"read '{best_read}'  -> {name}")

            if run_ffmpeg(src, dst, start, duration, args.crf, args.dry_run):
                made += 1
                entries.append({
                    "camera_id": cam,
                    "clip": name,
                    "read_as": best_read,
                    "confidence": round(best_conf, 2),
                    "entry_timestamp": visit["first_seen"].isoformat(),
                    "exit_timestamp": visit["last_seen"].isoformat(),
                    "source_start_sec": round(start, 3),
                    "source_end_sec": round(end, 3),
                    "clip_duration_sec": round(duration, 3),
                    # Where the vehicle actually enters/leaves inside the clip,
                    # so the player can highlight it past the padding.
                    "vehicle_in_at": round(start_raw - start, 3),
                    "vehicle_out_at": round(end_raw - start, 3),
                    "all_reads": [p for p, _ in visit["reads"]],
                })
            else:
                failed += 1

        if entries:
            manifest[plate] = {"plate": plate,
                               "cameras": [e["camera_id"] for e in entries],
                               "clips": entries}

    if not args.dry_run:
        # The manifest is metadata the dashboard reads at boot, so it ships with
        # index.html rather than sitting among the video files.
        os.makedirs(os.path.dirname(args.manifest) or ".", exist_ok=True)
        path = args.manifest
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        total_mb = sum(
            os.path.getsize(os.path.join(args.out, f))
            for f in os.listdir(args.out) if f.endswith(".mp4")) / 1e6

        print(f"\n{'='*80}")
        print(f"  Clips written : {made}   failed/skipped: {failed}")
        print(f"  Vehicles      : {len(manifest)}")
        print(f"  Total size    : {total_mb:.1f} MB")
        print(f"  Manifest      : {path}")
        print(f"{'='*80}\n")
    else:
        print(f"\n  dry run — {made} clip(s) would be written\n")


if __name__ == "__main__":
    main()
