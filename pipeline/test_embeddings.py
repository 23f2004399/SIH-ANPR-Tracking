#!/usr/bin/env python3
"""
Vehicle Re-ID Embedding Accuracy Evaluation
===========================================
SIH Problem Statement: 26127 (Bharat Electronics Limited)

Evaluates the retrieval accuracy of generated Re-ID embeddings by matching
sample crops from 'sample_crops/' against the gallery embeddings in 'crops/vehicles/'.

Metrics Evaluated:
- Top-1 Accuracy (%): Correct vehicle identity is the #1 nearest neighbor.
- Top-K Accuracy (%): Correct vehicle identity is within the top K nearest neighbors.
- Mean Reciprocal Rank (MRR): Average of 1 / rank of the ground-truth match.
- Cosine Similarity Separation Margin: True Match Similarity vs. Hardest False Match Similarity.

Usage:
    python pipeline/test_embeddings.py
    python pipeline/test_embeddings.py --output_dir ./outputs
    python pipeline/test_embeddings.py --crops_dir ./outputs/crops/vehicles --samples_dir ./outputs/sample_crops
    python pipeline/test_embeddings.py --verbose
"""

import os
import sys
import glob
import re
import argparse
import time
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark and evaluate Vehicle Re-ID embedding retrieval accuracy"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./outputs",
        help="Base output directory from main.py (default: ./outputs)"
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
        "--model",
        type=str,
        default="resnet18",
        help="Re-ID feature extractor model (default: resnet18)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Compute device ('cuda', 'cpu', or leave blank for auto)"
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=5,
        help="Top-K accuracy evaluation cutoff (default: 5)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed per-vehicle match results"
    )
    return parser.parse_args()


def load_gallery(crops_dir: str) -> Tuple[List[str], np.ndarray, Dict[str, str]]:
    """
    Load all precomputed .npy embeddings from the gallery directory.
    Returns:
        gallery_keys: list of unique vehicle identifiers (e.g. 'Camera_1_track_12')
        gallery_matrix: (N, 512) normalized numpy array
        crop_image_paths: dict mapping key to image file path
    """
    if not os.path.isdir(crops_dir):
        return [], np.empty((0, 512)), {}

    emb_files = sorted(glob.glob(os.path.join(crops_dir, "*_emb.npy")))
    if not emb_files:
        return [], np.empty((0, 512)), {}

    gallery_keys = []
    gallery_embs = []
    crop_images = {}

    for fpath in emb_files:
        fname = os.path.basename(fpath)
        # Extract identifier e.g. "Camera_1_track_1013_emb.npy" -> "Camera_1_track_1013"
        key = fname[:-8] if fname.endswith("_emb.npy") else os.path.splitext(fname)[0]

        try:
            vec = np.load(fpath).astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            else:
                continue
        except Exception as e:
            print(f"[WARN] Could not load embedding {fpath}: {e}")
            continue

        img_path = os.path.join(crops_dir, f"{key}.jpg")
        gallery_keys.append(key)
        gallery_embs.append(vec)
        crop_images[key] = img_path if os.path.exists(img_path) else ""

    gallery_matrix = np.array(gallery_embs, dtype=np.float32)
    return gallery_keys, gallery_matrix, crop_images


def discover_sample_queries(samples_dir: str, valid_keys: List[str]) -> List[Tuple[str, str]]:
    """
    Find sample query images in the samples directory.
    Supports both subfolder structure (sample_crops/Camera_1_track_1/sample_01.jpg)
    and flat file structure (sample_crops/Camera_1_track_1_sample_01.jpg).
    Returns list of (ground_truth_key, image_path).
    """
    if not os.path.isdir(samples_dir):
        return []

    valid_keys_set = set(valid_keys)
    queries = []

    # 1. Check for subfolder structure
    for entry in os.scandir(samples_dir):
        if entry.is_dir():
            track_key = entry.name
            if track_key in valid_keys_set:
                for img_file in glob.glob(os.path.join(entry.path, "*.jpg")):
                    queries.append((track_key, img_file))

    # 2. Check for flat structure
    flat_images = glob.glob(os.path.join(samples_dir, "*.jpg"))
    for fpath in flat_images:
        fname = os.path.basename(fpath)
        # Match pattern like (Camera_1_track_12)_sample_01.jpg
        match = re.match(r"^(.*)_sample_\d+\.jpg$", fname)
        if match:
            track_key = match.group(1)
            if track_key in valid_keys_set:
                queries.append((track_key, fpath))

    return queries


def main():
    args = parse_args()

    crops_dir = args.crops_dir or os.path.join(args.output_dir, "crops", "vehicles")
    samples_dir = args.samples_dir or os.path.join(args.output_dir, "sample_crops")

    print("\n" + "="*75)
    print(" 🚗 VEHICLE RE-ID EMBEDDING RETRIEVAL ACCURACY BENCHMARK")
    print("="*75)
    print(f"  Gallery Directory : {crops_dir}")
    print(f"  Samples Directory : {samples_dir}")
    print(f"  Model             : {args.model.upper()}")
    print("="*75)

    # 1. Load Gallery
    gallery_keys, gallery_matrix, _ = load_gallery(crops_dir)
    if len(gallery_keys) == 0:
        print(f"\n[ERROR] No gallery embeddings (*_emb.npy) found in: {crops_dir}")
        print("Please run 'python pipeline/main.py' first to process videos and generate crops.\n")
        sys.exit(1)

    print(f"✅ Loaded {len(gallery_keys)} gallery vehicle embeddings ({gallery_matrix.shape[1]}-d vectors).")

    # 2. Discover Query Samples
    queries = discover_sample_queries(samples_dir, gallery_keys)
    if not queries:
        print(f"\n[ERROR] No matching sample queries found in: {samples_dir}")
        print(f"Checked for subfolders or images matching the {len(gallery_keys)} gallery vehicle keys.")
        print("Make sure 'pipeline/main.py' was run with sample saving enabled.\n")
        sys.exit(1)

    print(f"✅ Found {len(queries)} query sample crops across {len(set(k for k, _ in queries))} vehicles.")

    # 3. Load Re-ID Model for Query Feature Extraction
    device = args.device if args.device else None
    print(f"⚙️  Loading Re-ID Feature Extractor [{args.model}]...")
    reid_model = get_reid_model(args.model, device=device)

    # 4. Evaluation Loop
    top1_correct = 0
    topk_correct = 0
    reciprocal_ranks = []
    true_match_sims = []
    hardest_false_sims = []

    per_vehicle_stats = defaultdict(lambda: {"total": 0, "top1": 0, "topk": 0})
    key_to_idx = {k: i for i, k in enumerate(gallery_keys)}

    print(f"\nEvaluating {len(queries)} query crops against {len(gallery_keys)} gallery vehicles...\n")
    start_time = time.time()

    for idx, (gt_key, img_path) in enumerate(queries, start=1):
        crop_img = cv2.imread(img_path)
        if crop_img is None or crop_img.size == 0:
            continue

        # Extract 512-d embedding
        q_emb = np.array(reid_model.get_embedding(crop_img), dtype=np.float32)
        q_norm = np.linalg.norm(q_emb)
        if q_norm > 0:
            q_emb = q_emb / q_norm

        # Cosine similarity against all gallery embeddings
        sims = np.dot(gallery_matrix, q_emb)

        # Rank in descending order of similarity
        ranked_indices = np.argsort(-sims)
        gt_idx = key_to_idx[gt_key]
        rank = int(np.where(ranked_indices == gt_idx)[0][0]) + 1

        is_top1 = (rank == 1)
        is_topk = (rank <= args.top_k)

        top1_correct += int(is_top1)
        topk_correct += int(is_topk)
        reciprocal_ranks.append(1.0 / rank)

        # Track cosine similarities
        true_sim = float(sims[gt_idx])
        true_match_sims.append(true_sim)

        # Hardest negative (highest similarity among all incorrect vehicles)
        if len(sims) > 1:
            hardest_false_idx = ranked_indices[0] if ranked_indices[0] != gt_idx else ranked_indices[1]
            hardest_false_sims.append(float(sims[hardest_false_idx]))

        per_vehicle_stats[gt_key]["total"] += 1
        per_vehicle_stats[gt_key]["top1"] += int(is_top1)
        per_vehicle_stats[gt_key]["topk"] += int(is_topk)

        if args.verbose:
            status = "✅ PASS (Rank 1)" if is_top1 else (f"🟡 TOP-{args.top_k} (Rank {rank})" if is_topk else f"❌ FAIL (Rank {rank})")
            top_match_key = gallery_keys[ranked_indices[0]]
            print(f"  [{idx:03d}/{len(queries):03d}] {gt_key:<26} -> {status:<18} | Top Match: {top_match_key} ({sims[ranked_indices[0]]:.3f})")

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

    # 5. Output Summary Report
    print("\n" + "="*75)
    print(" 📊 RE-ID RETRIEVAL ACCURACY REPORT")
    print("="*75)
    print(f"  Total Gallery Vehicles Tested : {len(gallery_keys):,}")
    print(f"  Total Query Samples Evaluated : {total_eval:,}")
    print(f"  Evaluation Time               : {elapsed:.2f}s ({total_eval / max(elapsed, 0.001):.1f} queries/sec)")
    print("-" * 75)
    print(f"  🏆 Top-1 Accuracy             : {top1_acc:6.2f}%  ({top1_correct}/{total_eval})")
    print(f"  🎯 Top-{args.top_k} Accuracy             : {topk_acc:6.2f}%  ({topk_correct}/{total_eval})")
    print(f"  📈 Mean Reciprocal Rank (MRR) : {mrr:6.4f}")
    print("-" * 75)
    print(f"  🔹 Avg True Match Cosine Sim  : {avg_true_sim:.4f}")
    print(f"  🔸 Avg Hardest False Cosine Sim: {avg_false_sim:.4f}")
    print(f"  ✨ Separation Margin (Δ)      : {margin:+.4f}")
    print("="*75)

    if top1_acc >= 80.0:
        print("  🎉 Benchmark Result: EXCELLENT retrieval discrimination.")
    elif top1_acc >= 60.0:
        print("  👍 Benchmark Result: GOOD retrieval discrimination.")
    else:
        print("  ⚠️ Benchmark Result: Moderate discrimination. Consider fine-tuning Re-ID model.")
    print("="*75 + "\n")


if __name__ == "__main__":
    main()
