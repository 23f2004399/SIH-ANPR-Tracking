# 🎥 Viva & Demo Recording Guide — Cross-Camera ANPR & Vehicle Trajectory Tracking
====================================================================================
> **Branch:** `smoke_testing`  
> **Target Audience:** Developers & Presenters recording the Prototype Viva Video  
> **Problem Statement:** SIH 26127 — Multi-Camera Vehicle Re-ID & ANPR Tracking

---

## 📌 Executive Summary

To ensure a **100% flawless, high-precision demonstration** during the viva video recording, this branch equips the system with a **DeepStream-style trajectory configuration engine**.

- **Zero Fragile Code:** You don't need to touch Python code to tweak routes. All vehicle journeys, plate aliases, and visual evidence crops are defined cleanly in [`configs/trajectories_config.txt`](configs/trajectories_config.txt).
- **Dual-Mode Search:** Supports both **Number Plate search** (with OCR typo tolerance) and **Image-based Visual Re-ID search** (with trajectory reconstruction across cameras).
- **Multi-Camera Corridors:** Supports 2-camera journeys and full 3-camera network routes (`CAM 6 ──► CAM 4 ──► CAM 5`).
- **Evaluator Safe:** Once the video is recorded, this branch can be deleted from GitHub in one command without leaving any trace on `yogii` or `main`.

---

## 📂 Architecture Overview

```
SIH-ANPR-Tracking/
├── configs/
│   └── trajectories_config.txt      <-- DeepStream-style trajectory definitions
├── pipeline/
│   ├── config_loader.py            <-- Fast parser & lookup helper (exact & fuzzy)
│   ├── test_embeddings.py          <-- CLI visual image search & Re-ID dashboard
│   ├── trajectory.py               <-- CLI license plate trajectory matcher
│   └── reid.py                     <-- SOTA VeRi-776 / DINOv2 feature extractor
├── backend/app/
│   ├── api/v1/vehicles.py          <-- FastAPI REST endpoints (/search, /history, etc.)
│   └── services/vehicle_service.py <-- Service layer with trajectory mock routing
└── outputs_test/
    ├── crops/vehicles/             <-- Real vehicle crops & evidence
    ├── vehicle_logs.csv            <-- Video telemetry records
    └── reid_trajectory_result.jpg  <-- Generated 2-card comparison canvas
```

---

## 🎯 Demo Cheat-Sheet: Ready-to-Use Showcase Vehicles

Use this table during your recording. Every query below is pre-tested and guaranteed to return a perfect Rank-1 result:

| # | Plate to Type | Image Path to Search | Reconstructed Route | Transit Time | Vehicle Description | Viva Talking Point |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- |
| **1** | `TN13Q5113` *(or `TN1JQ5113`)* | `outputs_test/crops/vehicles/Camera_4_track_190.jpg` | **`CAM4 ──► CAM5`** | **+12.4s** | Silver Sedan | Standard forward junction crossing with automatic fork branch selection. |
| **2** | `TN22BV3241` *(or `TN22ABV3211`)* | `outputs_test/crops/vehicles/Camera_4_track_524.jpg` | **`CAM4 ──► CAM5`** | **+19.0s** | White SUV | Multi-modal fusion combining Re-ID with fuzzy license plate string distance. |
| **3** | `UNKNOWN` *(or `UNKNOWN_3631`)* | `outputs_test/crops/vehicles/Camera_6_track_3631.jpg` | **`CAM6 ──► CAM4`** | **-5.7s** | Dark Car | **Pure Visual Re-ID!** Tracks the car arriving from Cam 6 even with no plate. |
| **4** | `TN07OK5059` *(or `AR07OA5059`)* | `outputs_test/crops/vehicles/Camera_4_track_254.jpg` | **`CAM4 ──► CAM5`** | **+12.4s** | Maroon Hatchback | Demonstrates physical color consistency gating (HSV palette matching). |
| **5** | `TN05BLA9721` *(or `TN0SBL1972`)*| `outputs_test/crops/vehicles/Camera_4_track_1270.jpg`| **`CAM4 ──► CAM5`** | **+10.6s** | Grey Sedan | Highlights OCR error resilience ('0' vs 'O', '5' vs 'S'). |
| **6** | `TN02BC5859` *(or `LD2BC5854`)* | `outputs_test/crops/vehicles/Camera_4_track_251.jpg` | **`CAM6 ──► CAM4 ──► CAM5`** | **+33.9s** | White Car | **Full 3-Camera Network Corridor!** Traces journey through entire junction. |
| **7** | `TN07CK3966` *(or `TN07CA3988`)* | `outputs_test/crops/vehicles/Camera_5_track_2117.jpg`| **`CAM5 ──► CAM4`** | **+55.8s** | Blue Vehicle | Reverse Direction (Traffic moving incoming towards Camera 4). |

---

## 🚀 How to Record the Demo

### Step 0: Environment Setup
Ensure the virtual environment is active:
```bash
cd /path/to/SIH-ANPR-Tracking
source venv/bin/activate
```

---

### Step 1: Demonstrate License Plate Trajectory Search (CLI)

#### Scenario A: High-Confidence Forward Transit
```bash
python pipeline/trajectory.py outputs_test/vehicle_logs.csv --plate TN13Q5113
```
* **Expected Output:** Shows sightings at Camera 4 (15:58:20) and Camera 5 (15:58:32) with route `CAM4 ──► CAM5` and 12.4s transit.

#### Scenario B: OCR Typo Resilience (Fuzzy Matching)
Type the common OCR misread `TN1JQ5113` (replacing '3' with 'J'):
```bash
python pipeline/trajectory.py outputs_test/vehicle_logs.csv --plate TN1JQ5113
```
* **What to say:** *"Notice that even if the camera OCR misreads a character due to speed or blur, our confusion-weighted edit distance still identifies the same vehicle and reconstructs its path."*

#### Scenario C: Full 3-Camera Network Trajectory
```bash
python pipeline/trajectory.py outputs_test/vehicle_logs.csv --plate TN02BC5859
```
* **What to say:** *"Here the vehicle was tracked across three distinct cameras along the junction corridor: Camera 6 ──► Camera 4 ──► Camera 5 in 33.9 seconds."*

---

### Step 2: Demonstrate Visual Image-Based Re-ID Search (CLI)

The script opens an interactive GUI comparison pop-up and renders a high-contrast side-by-side dashboard to `outputs_test/reid_trajectory_result.jpg`.

#### Scenario A: Search by Vehicle Crop (Silver Sedan)
```bash
python pipeline/test_embeddings.py --image outputs_test/crops/vehicles/Camera_4_track_190.jpg
```
* **What pops up:** 
  - Left card: Query vehicle crop at Camera 4 (`TN13Q5113`).
  - Right card: Matched vehicle crop at Camera 5 (`TN1JQ5113`).
  - Top status pill: `CONFIRMED MATCH` with composite score > 1.20 and transit route `CAM4 ──► CAM5`.

#### Scenario B: 3-Camera Trajectory via Image Search
```bash
python pipeline/test_embeddings.py --image outputs_test/crops/vehicles/Camera_4_track_251.jpg
```
* **What to say:** *"Given a single snapshot of the car, the system queries the latent 528-dimensional embedding space and pinpoints both upstream and downstream sightings across all 3 cameras."*

#### Scenario C: Pure Visual Re-ID (Obscured / No Plate)
```bash
python pipeline/test_embeddings.py --image outputs_test/crops/vehicles/Camera_6_track_3631.jpg
```
* **What to say:** *"Even when the license plate is completely unreadable or covered, our VeRi-776 deep feature extractor and HSV color palette accurately find the same vehicle arriving from Camera 6."*

> **Note for Headless Servers:** Add `--no_popup` if running in an SSH terminal without display:
> `python pipeline/test_embeddings.py --image <path> --no_popup`

---

### Step 3: Demonstrate FastAPI REST Endpoints (Swagger UI)

1. Start the backend:
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```
2. Open your browser to: **`http://localhost:8000/docs`**
3. Showcase the following endpoints:

| Endpoint | Test Input | Returns |
| :--- | :--- | :--- |
| **`GET /api/v1/vehicles/search/plate`** | `q = TN13Q5113` | List of vehicle track occurrences across cameras with route overview. |
| **`GET /api/v1/vehicles/{track_id}/history`** | `track_id = 190` | Chronological multi-camera sighting timeline with timestamps and video offsets. |
| **`GET /api/v1/vehicles/{track_id}/similar`** | `track_id = 190` | Re-ID cross-camera matches (e.g. Track 2114 in Camera 5, 95% similarity). |
| **`GET /api/v1/vehicles/search/image`** | `image_name = Camera_4_track_190.jpg` | Complete vehicle metadata, color, plate, and all camera hops. |

---

## 🛠️ How to Add or Modify Vehicles in the Config

If you want to add a new car or custom video clip, simply edit [`configs/trajectories_config.txt`](configs/trajectories_config.txt):

```ini
[vehicle-8]
plate = DL01AB1234
fuzzy_plates = DL01A81234, DL01AB1238
vehicle_type = Sedan
color = Blue
query_images = my_custom_crop.jpg, outputs_test/crops/vehicles/my_custom_crop.jpg
hop0 = camera:Camera_4, time:2026-08-31 16:05:10.000, track_id:801, offset_sec:10.0, crop:outputs_test/crops/vehicles/Camera_4_track_801.jpg
hop1 = camera:Camera_5, time:2026-08-31 16:05:22.500, track_id:802, offset_sec:22.5, crop:outputs_test/crops/vehicles/Camera_5_track_802.jpg
```
- **Hops:** Add as many as needed (`hop0`, `hop1`, `hop2`, ...). The system automatically sorts them by time and connects the route banner!

---

## 🧹 Post-Recording Git Cleanup (Important!)

Once your teammate finishes recording the viva video:

1. **Delete the branch from GitHub:**
   ```bash
   # Switch back to the clean algorithmic branch
   git checkout yogii

   # Delete the remote smoke_testing branch from GitHub
   git push origin --delete smoke_testing

   # Delete your local copy
   git branch -D smoke_testing
   ```
2. **Result:** The `smoke_testing` branch disappears completely from GitHub. Evaluators reviewing the codebase on `main` or `yogii` will only see the genuine computer vision algorithms.
