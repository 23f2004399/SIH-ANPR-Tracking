#!/usr/bin/env python3
"""
Fast Re-ID Embedding Regenerator
================================================================================
Recomputes and updates all vehicle embeddings (*_emb.npy) directly from existing
crop images (*.jpg) in the output directory without rerunning video decoding,
tracking, or OCR.

Key Features:
- Uses Upgraded Hybrid Re-ID (Deep Features + Normalized Central HSV Color Palette).
- Highly optimized batch inference using PyTorch (get_batch_embeddings).
- Works with ResNet18, ResNet50, or DINOv2.
- In-place updates: overwrites existing embeddings with accurate, color-aware vectors.
"""

import os
import sys
import glob
import time
import argparse
from typing import List

import cv2
import numpy as np
import torch

# Ensure repo root and pipeline/ are on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
for p in (REPO_ROOT, SCRIPT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from pipeline.reid import get_reid_model


def parse_args():
    parser = argparse.ArgumentParser(
        description="Regenerate Re-ID vehicle embeddings from existing crop images"
    )
    parser.add_argument(
        "--crops_dir",
        type=str,
        default="",
        help="Path to vehicle crops folder (defaults to ./outputs_test/crops/vehicles or ./outputs/crops/vehicles)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="veri776",
        help="Feature extractor backbone: 'veri776' (SOTA VeRi-776 Re-ID), 'dinov2', 'resnet50', 'resnet18' (default: veri776)"
    )
    parser.add_argument(
        "--hybrid_color",
        action="store_true",
        default=True,
        help="Enable hybrid color-aware feature fusion (default: True)"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=64,
        help="Batch size for feature extraction (default: 64)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Compute device ('cuda', 'cpu', or leave blank for auto)"
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Run without saving changes to disk"
    )
    return parser.parse_args()


def resolve_crops_dir(crops_dir_arg: str) -> str:
    """Auto-detect crops directory if not provided."""
    if crops_dir_arg and os.path.isdir(crops_dir_arg):
        return os.path.abspath(crops_dir_arg)

    candidates = [
        "./outputs_test/crops/vehicles",
        "./outputs/crops/vehicles"
    ]
    for c in candidates:
        if os.path.isdir(c) and glob.glob(os.path.join(c, "*.jpg")):
            return os.path.abspath(c)

    return os.path.abspath("./outputs/crops/vehicles")


def main():
    args = parse_args()
    crops_dir = resolve_crops_dir(args.crops_dir)

    print("\n" + "=" * 78)
    print(" 🚗 FAST VEHICLE RE-ID EMBEDDING REGENERATOR")
    print("=" * 78)
    print(f"  Crops Directory : {crops_dir}")
    print(f"  Model Backbone  : {args.model.upper()}")
    print(f"  Hybrid Color    : {'ENABLED (85% Deep + 15% HSV Palette)' if args.hybrid_color else 'DISABLED'}")
    print(f"  Batch Size      : {args.batch_size}")
    print("=" * 78)

    if not os.path.isdir(crops_dir):
        print(f"[ERROR] Crops directory not found: {crops_dir}")
        sys.exit(1)

    # Discover all crop images
    crop_files = sorted(glob.glob(os.path.join(crops_dir, "*.jpg")))
    total_crops = len(crop_files)

    if total_crops == 0:
        print(f"[ERROR] No vehicle crop images (*.jpg) found in: {crops_dir}")
        sys.exit(1)

    print(f"✅ Found {total_crops:,} vehicle crop images to process.")

    # Initialize Re-ID model
    device = args.device if args.device else ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"⚙️  Loading Re-ID model [{args.model}] on {device}...")
    reid_model = get_reid_model(model_name=args.model, device=device, hybrid_color=args.hybrid_color)

    batch_size = max(1, args.batch_size)
    start_time = time.time()
    processed_count = 0
    saved_count = 0

    print(f"\n🚀 Regenerating embeddings in batches of {batch_size}...\n")

    for i in range(0, total_crops, batch_size):
        batch_paths = crop_files[i:i + batch_size]
        batch_imgs = []
        valid_paths = []

        # Load images
        for p in batch_paths:
            img = cv2.imread(p)
            if img is not None and img.size > 0:
                batch_imgs.append(img)
                valid_paths.append(p)
            else:
                print(f"⚠️  Skipping unreadable crop: {p}")

        if not batch_imgs:
            continue

        # Extract embeddings in batch
        if hasattr(reid_model, "get_batch_embeddings"):
            batch_embs = reid_model.get_batch_embeddings(batch_imgs, batch_size=batch_size)
        else:
            batch_embs = np.array([reid_model.get_embedding(im) for im in batch_imgs], dtype=np.float32)

        # Save each embedding to disk
        if not args.dry_run:
            for p, emb_vec in zip(valid_paths, batch_embs):
                base, _ = os.path.splitext(p)
                emb_path = f"{base}_emb.npy"
                np.save(emb_path, emb_vec.astype(np.float32))
                saved_count += 1
        else:
            saved_count += len(valid_paths)

        processed_count += len(valid_paths)

        # Progress reporting
        pct = (processed_count / total_crops) * 100.0
        elapsed = time.time() - start_time
        rate = processed_count / max(elapsed, 0.001)
        eta_sec = (total_crops - processed_count) / max(rate, 0.001)

        sys.stdout.write(
            f"\r  Progress: [{processed_count:4d}/{total_crops:4d}] ({pct:5.1f}%) | "
            f"Rate: {rate:5.1f} img/s | Elapsed: {elapsed:4.1f}s | ETA: {eta_sec:4.1f}s"
        )
        sys.stdout.flush()

    total_time = time.time() - start_time
    emb_dim = batch_embs.shape[1] if total_crops > 0 else 0

    print("\n\n" + "=" * 78)
    print(" 🎉 EMBEDDING REGENERATION COMPLETE!")
    print("=" * 78)
    print(f"  Total Images Processed : {processed_count:,}")
    print(f"  Total Embeddings Saved : {saved_count:,} (*_emb.npy)")
    print(f"  Embedding Vector Dim   : {emb_dim}-d (L2-Normalized)")
    print(f"  Total Time Taken       : {total_time:.2f}s ({processed_count / max(total_time, 0.001):.1f} crops/sec)")
    print(f"  Destination Folder     : {crops_dir}")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()

