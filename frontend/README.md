# ZyroTrace AI — Next.js Full-Stack Application

Production-grade, fully functional Next.js full-stack port of the ZyroTrace AI surveillance and city traffic analytics dashboard, connected directly to the FastAPI backend defined in `doc.json`.

---

## 🚀 Quick Start

### 1. Run Next.js Frontend
```bash
cd frontend
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 2. Run FastAPI Backend (Optional / Local Dev)
```bash
uvicorn backend.app.main:app --reload --port 8000
```
API docs will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 🏛️ Architecture & Highlights

- **Pixel-Perfect Fidelity**: Preserves 100% of the prototype UI design, typography (`Instrument Sans`, `JetBrains Mono`), color palettes, SVG coordinate maps, animations (`zbreathe`, `zsweep`), and layout metrics.
- **Strict FastAPI Connectivity**: Direct API communication layer via Next.js rewrites (`/api/v1/:path*` -> `http://127.0.0.1:8000`), preventing cross-origin CORS barriers in dev/prod.
- **Two Core Modes**:
  1. **Police Surveillance (`police`)**:
     - Live Camera feed HUD overlay with bounding box telemetry (Node 26, 41 detections/min, CAR / 2W / TRUCK occlusions).
     - Number Plate search & nearest-neighbour visual embedding vehicle crop Re-ID.
     - Multi-node detection matrix (18 sightings across 11 camera nodes with paginated cards).
     - Interactive vector route map with numbered pins (1–4), GPS coordinates, and real-time corridor playback.
     - Movement history drawer with speeds, dwell intervals, and one-click **Official Certified Police Dossier PDF Export**.
     - Alert Center dropdown with active threat interventions (Cloned Plate, Missing Plate, Blacklist Hit).
  2. **City Traffic Analytics (`urban`)**:
     - Congestion level, active choke points, vehicle count, and idle CO₂ metrics.
     - Arterial road congestion heatmap & flow dynamics SVG with arterial speed markers.
     - Fleet mix per corridor percentage distribution.
     - Vehicle classification conic-gradient donut chart.
     - Carbon footprint idle hour breakdown.
     - AI-driven signal control policy recommendations.

---

## 🛠️ Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript (Strict typing)
- **Styling**: Tailwind CSS + Custom Design Tokens + Print Styles
- **Backend API**: FastAPI (`/api/v1/cameras`, `/api/v1/traffic/*`, `/api/v1/vehicles/*`)
