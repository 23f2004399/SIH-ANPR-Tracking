#!/usr/bin/env python3
"""
Cross-Camera Vehicle Trajectory Matcher
========================================
Reads outputs/vehicle_logs.csv and finds the same vehicle across different
cameras using fuzzy plate matching, then reports where and when it was seen.

Matching is confusion-aware rather than a plain string ratio: OCR reliably
mixes up O/0, I/1, B/8, D/T and friends, so those substitutions cost far less
than an unrelated character. 'DN07OL9722' and 'TN07OL9722' are the same car;
'TN1234' and 'TN5678' are not, even though both differ by four characters.

Usage:
    python trajectory.py                          # all cross-camera matches
    python trajectory.py --threshold 0.70         # looser matching (default 0.75)
    python trajectory.py --plate TN07OL9722       # trace one vehicle
    python trajectory.py --min_len 9              # ignore short partial reads
    python trajectory.py --max_gap 600            # max seconds between sightings
"""

import os, csv, argparse, itertools
from collections import defaultdict
from datetime import datetime

from ocr import TO_DIGIT, LETTER_SIM, correct_indian_plate

TS_FMT = "%Y-%m-%d %H:%M:%S.%f"

# Character pairs OCR routinely swaps. Built from the same confusion tables the
# recogniser uses, so the matcher forgives exactly the errors it tends to make.
def _build_confusable() -> set:
    pairs = set()
    for letter, digit in TO_DIGIT.items():          # O/0, I/1, B/8, ...
        pairs.add(frozenset((letter, digit)))
    for a, similar in LETTER_SIM.items():           # I/T, K/N, M/N, ...
        for b in similar:
            if a != b:
                pairs.add(frozenset((a, b)))
    return pairs

CONFUSABLE = _build_confusable()
CONFUSION_COST = 0.3     # a known OCR swap is cheap
SUBSTITUTE_COST = 1.0    # an unrelated character is not


def sub_cost(a: str, b: str) -> float:
    if a == b:
        return 0.0
    return CONFUSION_COST if frozenset((a, b)) in CONFUSABLE else SUBSTITUTE_COST


def similarity(a: str, b: str) -> float:
    """
    Confusion-weighted edit distance, normalised to a 0..1 similarity.

    Plain Levenshtein treats 'D'->'T' (a routine OCR slip) the same as 'D'->'9'
    (a different vehicle). Weighting substitutions by how confusable the glyphs
    are keeps real matches above the threshold without dragging in noise.
    """
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(
                prev[j] + 1,                       # deletion
                cur[j - 1] + 1,                    # insertion
                prev[j - 1] + sub_cost(ca, cb),    # substitution
            ))
        prev = cur
    return max(0.0, 1.0 - prev[-1] / max(len(a), len(b)))


class Sighting:
    """One vehicle seen at one camera, merged across its repeated track IDs."""

    __slots__ = ("camera", "plate", "first_seen", "last_seen", "tracks", "conf")

    def __init__(self, camera, plate, first_seen, last_seen, track_id, conf):
        self.camera = camera
        self.plate = plate
        self.first_seen = first_seen
        self.last_seen = last_seen
        self.tracks = [track_id]
        self.conf = conf

    def absorb(self, first_seen, last_seen, track_id, conf):
        self.first_seen = min(self.first_seen, first_seen)
        self.last_seen = max(self.last_seen, last_seen)
        self.tracks.append(track_id)
        self.conf = max(self.conf, conf)

    def __repr__(self):
        return f"{self.camera}:{self.plate}@{self.first_seen:%H:%M:%S}"


def load_sightings(path, min_len, min_conf):
    """Read the log and merge repeated track IDs of the same plate per camera."""
    if not os.path.isfile(path):
        raise SystemExit(f"[ERROR] Log not found: {path}")

    merged, skipped_short, skipped_conf = {}, 0, 0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            plate = (row.get("plate_number") or "").strip().upper()
            if not plate or plate in ("UNKNOWN", "DETECTING...", "RECOGNIZING..."):
                continue
            if len(plate) < min_len:
                skipped_short += 1
                continue
            try:
                conf = float(row.get("average_ocr_confidence") or 0.0)
            except ValueError:
                conf = 0.0
            if conf < min_conf:
                skipped_conf += 1
                continue
            try:
                entry = datetime.strptime(row["entry_timestamp"], TS_FMT)
                exit_ = datetime.strptime(row["exit_timestamp"], TS_FMT)
            except (KeyError, ValueError):
                continue

            cam = row["camera_id"]
            key = (cam, plate)
            if key in merged:
                merged[key].absorb(entry, exit_, row.get("track_id", "?"), conf)
            else:
                merged[key] = Sighting(cam, plate, entry, exit_,
                                       row.get("track_id", "?"), conf)

    return list(merged.values()), skipped_short, skipped_conf


def find_matches(sightings, threshold, max_gap):
    """Every cross-camera pair of sightings whose plates match closely enough."""
    matches = []
    for a, b in itertools.combinations(sightings, 2):
        if a.camera == b.camera:
            continue                                # same camera is not a journey
        score = similarity(a.plate, b.plate)
        if score < threshold:
            continue
        first, second = (a, b) if a.first_seen <= b.first_seen else (b, a)
        gap = (second.first_seen - first.last_seen).total_seconds()
        if max_gap and gap > max_gap:
            continue
        matches.append((score, first, second, gap))
    matches.sort(key=lambda m: (-m[0], m[1].first_seen))
    return matches


def build_trajectories(matches):
    """
    Chain pairwise matches into multi-camera journeys.

    A vehicle crossing three cameras shows up as three separate pairs; union-find
    collapses them into one trajectory so the report reads as a route rather than
    a list of disconnected hops.
    """
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for _, first, second, _ in matches:
        union((first.camera, first.plate), (second.camera, second.plate))

    groups = defaultdict(list)
    lookup = {}
    for _, first, second, _ in matches:
        for s in (first, second):
            lookup[(s.camera, s.plate)] = s
    for key, sighting in lookup.items():
        groups[find(key)].append(sighting)

    trajectories = []
    for members in groups.values():
        if len({s.camera for s in members}) < 2:
            continue                                # never left one camera
        # Collapse per camera. Several fuzzy variants of one plate at the same
        # camera ('TN67CY7549', 'TN67O7549') are one visit, not three hops —
        # without this the route reads 'CAM2 -> CAM2 -> CAM2' with negative gaps.
        per_camera = {}
        for s in members:
            visit = per_camera.get(s.camera)
            if visit is None:
                per_camera[s.camera] = {
                    "camera": s.camera,
                    "first_seen": s.first_seen,
                    "last_seen": s.last_seen,
                    "reads": [(s.plate, s.conf)],
                    "tracks": len(s.tracks),
                }
            else:
                visit["first_seen"] = min(visit["first_seen"], s.first_seen)
                visit["last_seen"] = max(visit["last_seen"], s.last_seen)
                visit["reads"].append((s.plate, s.conf))
                visit["tracks"] += len(s.tracks)

        visits = sorted(per_camera.values(), key=lambda v: v["first_seen"])
        for v in visits:
            v["reads"].sort(key=lambda r: -r[1])     # best read first
        # Label the route with its most trustworthy read: prefer a plate that is
        # a well-formed Indian registration, then highest OCR confidence.
        best = max(members, key=lambda s: (correct_indian_plate(s.plate)[1], s.conf))
        trajectories.append((best.plate, visits))
    trajectories.sort(key=lambda t: t[1][0]["first_seen"])
    return trajectories


def report(trajectories, matches, out_csv, threshold):
    print(f"\n{'='*94}")
    print(f"  CROSS-CAMERA TRAJECTORIES   |   {len(trajectories)} vehicle(s) "
          f"seen on 2+ cameras   |   threshold {threshold:.0%}")
    print(f"{'='*94}")

    if not trajectories:
        print("  No cross-camera matches. Try --threshold 0.65 or --min_len 7.\n")
    for plate, visits in trajectories:
        route = "  ->  ".join(v["camera"].replace("Camera_", "CAM") for v in visits)
        print(f"\n  ● {plate}     {route}")
        prev = None
        for v in visits:
            gap = ""
            if prev is not None:
                secs = (v["first_seen"] - prev["last_seen"]).total_seconds()
                gap = f"   (+{secs:.1f}s after {prev['camera'].replace('Camera_','CAM')})"
            best_read, best_conf = v["reads"][0]
            print(f"      {v['camera']:<10} {v['first_seen']:%H:%M:%S} -> "
                  f"{v['last_seen']:%H:%M:%S}   read '{best_read}' "
                  f"({best_conf:.1f}%)  tracks={v['tracks']}{gap}")
            others = [p for p, _ in v["reads"][1:]]
            if others:
                print(f"                   also read as: {', '.join(others)}")
            prev = v

    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["match_score", "plate_a", "camera_a", "a_entry", "a_exit",
                    "plate_b", "camera_b", "b_entry", "b_exit", "transit_seconds"])
        for score, first, second, gap in matches:
            w.writerow([
                f"{score:.3f}",
                first.plate, first.camera,
                first.first_seen.strftime(TS_FMT)[:-3], first.last_seen.strftime(TS_FMT)[:-3],
                second.plate, second.camera,
                second.first_seen.strftime(TS_FMT)[:-3], second.last_seen.strftime(TS_FMT)[:-3],
                f"{gap:.2f}",
            ])

    print(f"\n{'='*94}")
    print(f"  Pairwise matches : {len(matches)}")
    print(f"  CSV              : {out_csv}")
    print(f"{'='*94}\n")


def trace_one(sightings, target, threshold):
    """Show every camera whose read is close enough to a plate you name."""
    target = target.strip().upper()
    hits = sorted(((similarity(target, s.plate), s) for s in sightings),
                  key=lambda x: -x[0])
    hits = [(sc, s) for sc, s in hits if sc >= threshold]

    print(f"\n{'='*94}")
    print(f"  TRACE '{target}'   |   {len(hits)} sighting(s) at or above {threshold:.0%}")
    print(f"{'='*94}")
    if not hits:
        print("  Nothing matched. Try a lower --threshold.\n")
        return
    for score, s in sorted(hits, key=lambda x: x[1].first_seen):
        print(f"  {score:>6.1%}  {s.camera:<10} read '{s.plate:<12}' "
              f"{s.first_seen:%H:%M:%S} -> {s.last_seen:%H:%M:%S}  conf {s.conf:>5.1f}%")
    cams = {s.camera for _, s in hits}
    if len(cams) >= 2:
        ordered = sorted((s for _, s in hits), key=lambda s: s.first_seen)
        # Collapse repeat sightings at the same camera into one hop.
        hops = [s.camera for s in ordered]
        hops = [c for i, c in enumerate(hops) if i == 0 or c != hops[i - 1]]
        route = "  ->  ".join(c.replace("Camera_", "CAM") for c in hops)
        total = (ordered[-1].last_seen - ordered[0].first_seen).total_seconds()
        print(f"\n  ROUTE: {route}    (total {total:.1f}s across {len(cams)} cameras)")
    print()


def main():
    ap = argparse.ArgumentParser(description="Cross-camera vehicle trajectory matcher")
    ap.add_argument("log", nargs="?", default="./outputs/vehicle_logs.csv")
    ap.add_argument("--threshold", type=float, default=0.80,
                    help="Minimum plate similarity to call it the same vehicle (default 0.80). "
                         "0.75 lets 'TN07CL2138' match 'TN07OL2568' (0.77) — different cars. "
                         "The weakest genuine pair in this footage is 0.80.")
    ap.add_argument("--min_len", type=int, default=8,
                    help="Ignore plates shorter than this — short partial reads match "
                         "each other by accident (default 8)")
    ap.add_argument("--min_conf", type=float, default=0.0,
                    help="Ignore reads below this OCR confidence (default 0)")
    ap.add_argument("--max_gap", type=float, default=0.0,
                    help="Max seconds between two sightings to count as one journey "
                         "(0 = no limit)")
    ap.add_argument("--plate", default="", help="Trace a single plate instead of listing all")
    ap.add_argument("--output_csv", default="./outputs/trajectories.csv")
    args = ap.parse_args()

    sightings, skipped_short, skipped_conf = load_sightings(
        args.log, args.min_len, args.min_conf)

    print(f"\nLoaded {len(sightings)} unique camera+plate sighting(s) from {args.log}")
    if skipped_short:
        print(f"  skipped {skipped_short} read(s) shorter than {args.min_len} chars")
    if skipped_conf:
        print(f"  skipped {skipped_conf} read(s) below {args.min_conf}% confidence")

    if args.plate:
        trace_one(sightings, args.plate, args.threshold)
        return

    matches = find_matches(sightings, args.threshold, args.max_gap)
    trajectories = build_trajectories(matches)
    report(trajectories, matches, args.output_csv, args.threshold)


if __name__ == "__main__":
    main()
