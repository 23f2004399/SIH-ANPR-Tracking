# Phase 3 & 4 Backend Architecture Documentation

This document explains exactly how we implemented License Plate Search (Phase 3) and Vehicle Re-Identification (Phase 4), and where the code lives. We kept things very decoupled to make sure the web server stays fast and doesn't get bogged down by heavy AI models.

## Phase 3: License Plate Search

Our goal was to let users search for license plates, handle typos gracefully, and view the history of where a car has been.

### 1. The Database & Fuzzy Search (`backend/migrations/0002_phase3_4_schema.sql`)
We enabled the `pg_trgm` extension in PostgreSQL. This is what gives us "fuzzy matching". If the OCR engine misreads a `0` as an `O` (or vice versa), the database uses this extension to still find the closest match without breaking a sweat.

### 2. The Brain: Service Layer (`backend/app/services/vehicle_service.py`)
This file is where all the business logic lives. 
*   **Plate Normalization**: Before we even search the database, we run the user's search text through a function that strips out all spaces, dashes, and weird symbols, and turns everything uppercase (e.g., `dl 01-ab 1234` becomes `DL01AB1234`). This protects us from SQL injection and makes matching much more reliable.
*   **Timeline Building**: We added a function to grab every single time a specific car was seen across all cameras (`history`) and pull all the image crops saved for it (`evidence`).

### 3. The API Endpoints (`backend/app/api/v1/vehicles.py`)
We created the web endpoints that the frontend will actually talk to:
*   `GET /api/v1/vehicles/search/plate?q=...&exact=false`: Searches for a plate.
*   `GET /api/v1/vehicles/{track_id}/history`: Returns the chronological history of a vehicle.
*   `GET /api/v1/vehicles/{track_id}/evidence`: Returns the best crops (vehicle and plate images) for a specific track.


---


## Phase 4: Vehicle Re-Identification (Image Search)

Our goal here was to allow a user to click a car and find similar looking cars across the city, without killing our web server's performance.

### 1. The Heavy Lifter: Feature Extractor (`pipeline/reid.py` and `pipeline/main.py`)
*   **Strict Decoupling**: We explicitly kept heavy ML libraries like PyTorch and Ultralytics OUT of the `backend/` folder. They only exist in the `pipeline/` worker environment.
*   **The Model**: In `pipeline/reid.py`, we created a factory pattern that loads a lightweight ResNet18 model. It strips the final layer of the neural network so that instead of guessing *what* the object is, it outputs a raw list of 512 numbers (an "embedding" or mathematical fingerprint).
*   **Integration**: In `pipeline/main.py`, every time a vehicle track finishes, we pass the best crop to this model, get the 512 numbers, and save them alongside the image as a `.npy` file. 

### 2. The Vector Database (`backend/migrations/0002_phase3_4_schema.sql`)
We enabled the `pgvector` extension in PostgreSQL and created a `reid_embeddings` table. This allows Postgres to natively store our 512-number arrays and perform lightning-fast math (Cosine Distance) to find vectors that point in the same direction.

### 3. The Decoupled Search API (`backend/app/api/v1/vehicles.py` & `backend/app/services/vehicle_service.py`)
Since the backend doesn't have PyTorch, it can't generate a fingerprint for a randomly uploaded image. Instead, we built it so the user clicks an *existing* vehicle track they are looking at:
*   **`GET /api/v1/vehicles/{track_id}/similar`**: The frontend sends the `track_id`.
*   **The Logic**: The service fetches the *already-calculated* 512-number embedding for that track from the database. It then asks Postgres: *"Here are 512 numbers. Search the entire city and give me the top 10 cars with numbers that are mathematically closest to this."*
*   **Safety**: If the track doesn't have an embedding yet, the API gracefully returns a `404 Not Found` with a clear JSON error message instead of crashing the server.
