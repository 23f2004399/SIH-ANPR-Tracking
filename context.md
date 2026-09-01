# Project Context & Progress Report

**Project Title:** City-Wide AI Engine for Multi-Camera ANPR Trajectory Tracking and Urban Traffic Analytics  
**Hackathon:** Smart India Hackathon (SIH) — Internal Hackathon  
**Problem Statement ID:** SIH26127 (Ministry / Organization: Bharat Electronics Limited - BEL)  
**Hardware Profile:** NVIDIA GeForce GTX 1650 (4 GB VRAM), running Python on WSL/Linux  

---

## 1. What We're Working On

End-to-end AI pipeline to ingest multi-camera CCTV traffic streams and deliver:

1. **ANPR & OCR:** Detect and read Indian license plates across cameras.
2. **Cross-Camera Trajectory Tracking:** Track vehicles across geographically distributed camera nodes.
3. **Macro Traffic Analytics:** Density, corridor speeds, bottleneck detection.
4. **Law Enforcement Alerts:** Flag blacklisted vehicles and anomalous patterns.

---

## 2. What We Have Done Till Now

### A. Core Video Pipeline (`main.py`)
- **Vehicle Detection & Tracking:** YOLO11 (`yolo11n.pt`) + ByteTrack (`bytetrack.yaml`) for vehicle classes only.
- **License Plate Localization:** Fine-tuned YOLOv8 plate detector (`yolov8n_plate.pt`) auto-downloaded from Hugging Face and cached locally.
- **Crop Padding Fix:** Plate bounding boxes are expanded by 20% on all sides before cropping to prevent character truncation at edges.
- **Minimum Resolution Gate:** OCR is skipped on plates smaller than `16×40 px` (distant/blurry vehicles) to avoid noise reads.
- **OCR Engine (EasyOCR):** Switched from PaddleOCR (which failed on tight plate crops) to EasyOCR with an uppercase alphanumeric `allowlist`.
- **Two-Row Plate Support:** EasyOCR detections are sorted by Y-coordinate and concatenated top-to-bottom so `TN22` + `DM8143` → `TN22DM8143`.
- **3-Stage Bounding Box Tags:** `DETECTING...` (Orange) → `RECOGNIZING...` (Yellow) → `<PLATE> (conf%)` (Green).
- **Selective Crop Saving:** Only saves crops at track exit if confidence ≥ `--min_save_conf 40%`.
- **Unique Output Videos:** Output filenames derived from input stem (e.g. `outputs/annotated_CAM1_comp.mp4`).
- **CSV Logging:** `outputs/vehicle_logs.csv` with `[camera_id, track_id, entry_ts, exit_ts, plate, avg_conf]`.

### B. Standalone OCR Diagnostic (`ocr.py`)
- Batch-processes an entire plates folder or a single image.
- Preprocessing pipeline: padding → bicubic upscale (≥128 px) → CLAHE contrast → Otsu binarization (normal + inverted).
- EasyOCR with allowlist + Y-sorted multi-row concatenation.
- Exports results to `outputs/ocr_results.csv`.

### C. Vehicle Inspector (`visualize.py`)
- `python visualize.py <TRACK_ID>` shows side-by-side vehicle + plate crops.
- Exports an inspection card to `outputs/inspect_track_<ID>.jpg`.

### D. Gemini Vision OCR (`gemini.py`)
- Uses **Gemini 2.5 Flash** (free tier: 5 RPM, 20 RPD) to read plates from crop images via vision API.
- Prompts the model to output only uppercase alphanumeric characters.
- Exports results to `outputs/gemini_plates.csv`.
- Default delay of 13s between calls to stay safely under 5 RPM.

---

## 3. Current Problems & Blockers

### OCR Accuracy Still Not Perfect
EasyOCR (our current inline engine in `main.py`) is working but still makes errors on:
- Very short plates (partial reads like `8143` instead of `TN22DM8143`)
- Misreads due to font similarity (`O` vs `0`, `I` vs `1`, `B` vs `8`)
- Noisy/blurred crops from fast-moving vehicles

### Gemini Vision — Limited Free Tier
- `gemini-2.5-flash` works but is capped at **5 RPM and 20 RPD** on free tier.
- This means only ~20 plate images can be processed per day via Gemini.
- Groq was tried as an alternative but **all Groq vision models have been decommissioned** (as of Sep 2025, no vision models available on Groq).


---


## 5. Key Repository Structure

```
SIH_ANPR/
├── main.py           # Multi-Camera ANPR & Tracking Pipeline
├── ocr.py            # Standalone EasyOCR Batch Diagnostic Tool
├── gemini.py         # Gemini Vision Plate OCR (best accuracy)
├── visualize.py      # Plate & Vehicle Crop Inspector (by Track ID)
├── requirements.txt  # Python Dependencies
├── context.md        # This file
└── outputs/
    ├── annotated_*.mp4           # Annotated output videos
    ├── vehicle_logs.csv          # Trajectory & ANPR logs
    ├── gemini_plates.csv         # Gemini OCR results
    ├── ocr_results.csv           # EasyOCR batch results
    └── crops/
        ├── vehicles/             # Vehicle crops
        └── plates/               # License plate crops
```

---

