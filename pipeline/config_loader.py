#!/usr/bin/env python3
"""
DeepStream-Style Trajectory Config Loader
=========================================
Parses configs/trajectories_config.txt and provides lookup helpers for:
- Plate query (exact + fuzzy)
- Image query (file path, basename, or sample crop)
- Track ID query (camera + track_id)
"""

import os
import re
import difflib
import configparser
from datetime import datetime
from typing import List, Dict, Any, Optional

TS_FMT = "%Y-%m-%d %H:%M:%S.%f"
TS_FMT_NO_MS = "%Y-%m-%d %H:%M:%S"

CONFIG_PATH_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "configs",
    "trajectories_config.txt"
)


def _norm_plate(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'[^A-Za-z0-9]', '', str(text)).upper()


def _parse_time(ts_str: str) -> datetime:
    ts_str = ts_str.strip()
    for fmt in (TS_FMT, TS_FMT_NO_MS, "%H:%M:%S", "%H:%M:%S.%f"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            pass
    # Fallback to now
    return datetime.now()


def _parse_hop(val_str: str) -> Dict[str, Any]:
    """
    Parses comma-separated key:value hop string:
    camera:Camera_4, time:2026-08-31 15:58:20.200, track_id:190, offset_sec:20.2, crop:outputs_test/crops/vehicles/Camera_4_track_190.jpg
    """
    data = {}
    parts = [p.strip() for p in val_str.split(",") if p.strip()]
    for p in parts:
        if ":" in p:
            k, v = p.split(":", 1)
            k = k.strip().lower()
            v = v.strip()
            if k == "track_id":
                try:
                    data[k] = int(v)
                except ValueError:
                    data[k] = v
            elif k == "offset_sec":
                try:
                    data[k] = float(v)
                except ValueError:
                    data[k] = 0.0
            else:
                data[k] = v

    if "time" in data:
        data["datetime"] = _parse_time(data["time"])
    else:
        data["datetime"] = datetime.now()

    return data


def load_trajectory_configs(config_path: str = CONFIG_PATH_DEFAULT) -> List[Dict[str, Any]]:
    """Loads all vehicle trajectory sections from the config file."""
    if not os.path.isfile(config_path):
        return []

    cp = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
    cp.read(config_path, encoding="utf-8")

    vehicles = []
    for section in cp.sections():
        if not section.lower().startswith("vehicle"):
            continue

        raw = dict(cp.items(section))
        plate = raw.get("plate", "").strip().upper()
        fuzzy_raw = raw.get("fuzzy_plates", "")
        fuzzy_plates = [_norm_plate(p) for p in re.split(r'[,;]', fuzzy_raw) if p.strip()]
        if _norm_plate(plate) not in fuzzy_plates:
            fuzzy_plates.insert(0, _norm_plate(plate))

        v_type = raw.get("vehicle_type", "Vehicle").strip()
        color = raw.get("color", "Unknown").strip()

        img_raw = raw.get("query_images", "")
        query_images = [i.strip() for i in re.split(r'[,;]', img_raw) if i.strip()]

        # Parse hops: hop0, hop1, hop2, ...
        hops = []
        hop_keys = sorted([k for k in raw if k.startswith("hop")], key=lambda k: k)
        for hk in hop_keys:
            parsed = _parse_hop(raw[hk])
            hops.append(parsed)

        # Ensure hops are sorted chronologically by datetime
        hops.sort(key=lambda h: h["datetime"])

        # Build trajectory route string
        cams = [h.get("camera", "CAM").replace("Camera_", "CAM") for h in hops]
        route_str = " ──► ".join(cams)

        total_transit = 0.0
        if len(hops) >= 2:
            total_transit = (hops[-1]["datetime"] - hops[0]["datetime"]).total_seconds()

        vehicles.append({
            "section": section,
            "plate": plate,
            "norm_plate": _norm_plate(plate),
            "fuzzy_plates": fuzzy_plates,
            "vehicle_type": v_type,
            "color": color,
            "query_images": query_images,
            "query_image_basenames": [os.path.basename(i).lower() for i in query_images],
            "hops": hops,
            "route": route_str,
            "total_transit_seconds": total_transit
        })

    return vehicles


# Cached instance
_CACHED_CONFIGS: Optional[List[Dict[str, Any]]] = None


def get_all_demo_vehicles(reload: bool = False) -> List[Dict[str, Any]]:
    global _CACHED_CONFIGS
    if _CACHED_CONFIGS is None or reload:
        _CACHED_CONFIGS = load_trajectory_configs()
    return _CACHED_CONFIGS


def find_trajectory_by_plate(plate_query: str, threshold: float = 0.65) -> Optional[Dict[str, Any]]:
    """
    Finds a configured trajectory matching a plate query (exact, fuzzy list, or edit distance).
    """
    if not plate_query:
        return None

    norm_q = _norm_plate(plate_query)
    vehicles = get_all_demo_vehicles()

    # 1. Exact match on primary or fuzzy plates
    for v in vehicles:
        if norm_q in v["fuzzy_plates"] or norm_q == v["norm_plate"]:
            return v

    # 2. Substring match
    for v in vehicles:
        for p in v["fuzzy_plates"]:
            if len(norm_q) >= 4 and (norm_q in p or p in norm_q):
                return v

    # 3. Levenshtein ratio match
    best_v, best_sim = None, 0.0
    for v in vehicles:
        for p in v["fuzzy_plates"]:
            sim = difflib.SequenceMatcher(None, norm_q, p).ratio()
            if sim > best_sim:
                best_sim = sim
                best_v = v

    if best_sim >= threshold and best_v is not None:
        return best_v

    return None


def find_trajectory_by_image(image_path_or_name: str) -> Optional[Dict[str, Any]]:
    """
    Finds a configured trajectory matching an image path, basename, or sample crop.
    """
    if not image_path_or_name:
        return None

    clean_path = str(image_path_or_name).strip()
    bname = os.path.basename(clean_path).lower()
    vehicles = get_all_demo_vehicles()

    # 1. Direct path or basename match
    for v in vehicles:
        if bname in v["query_image_basenames"]:
            return v
        for q in v["query_images"]:
            if clean_path.endswith(q) or q.endswith(clean_path) or bname == os.path.basename(q).lower():
                return v

    # 2. Check if image matches any hop crop path or track key
    for v in vehicles:
        for hop in v["hops"]:
            crop_path = hop.get("crop", "")
            if crop_path and (bname == os.path.basename(crop_path).lower() or clean_path.endswith(crop_path)):
                return v
            # Match track key e.g. Camera_4_track_190
            cam = hop.get("camera", "")
            tid = hop.get("track_id", "")
            key = f"{cam}_track_{tid}".lower()
            if key in bname or key in clean_path.lower():
                return v

    return None


def find_trajectory_by_track(camera_id: str, track_id: Any) -> Optional[Dict[str, Any]]:
    """Finds trajectory by camera ID and track ID."""
    vehicles = get_all_demo_vehicles()
    cam_str = str(camera_id).strip().lower() if camera_id else ""
    t_str = str(track_id).strip()

    for v in vehicles:
        for hop in v["hops"]:
            hop_cam = str(hop.get("camera", "")).strip().lower()
            hop_tid = str(hop.get("track_id", "")).strip()
            if hop_tid == t_str:
                if not cam_str or hop_cam == cam_str:
                    return v
    return None
