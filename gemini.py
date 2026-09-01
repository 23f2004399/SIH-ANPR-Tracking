#!/usr/bin/env python3
"""
Gemini Vision License Plate Recognition
=========================================
Uses Google Gemini 2.0 Flash to read license plates from cropped images.

Usage:
    python gemini.py                          # process ./outputs/crops/plates/
    python gemini.py path/to/plates/          # custom directory
    python gemini.py path/to/plate.jpg        # single image
    python gemini.py --key YOUR_GEMINI_KEY    # or set GEMINI_API_KEY env var

Get a free key at: https://aistudio.google.com/apikey
Free tier: 15 RPM, 1500 requests/day  (more than enough for plate batches)
"""

import os, sys, glob, csv, time, argparse, base64
from pathlib import Path
import google.generativeai as genai

MODEL = "gemini-2.5-flash"

PROMPT = (
    "This is a cropped image of a vehicle license plate. "
    "Read ALL text on the plate — top row first, then bottom row. "
    "Output ONLY the alphanumeric characters (uppercase letters and digits), "
    "no spaces, no punctuation, no explanation. "
    "If no text is readable, output exactly: UNKNOWN"
)

def load_key(key_arg: str) -> str:
    key = key_arg or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("[ERROR] No Gemini API key found.")
        print("  Set env var : export GEMINI_API_KEY=your_key")
        print("  Or pass it  : python gemini.py --key YOUR_KEY")
        print("  Get free key: https://aistudio.google.com/apikey")
        sys.exit(1)
    return key

def read_plate(model, img_path: str, retry: int = 2) -> tuple[str, str]:
    """Send image to Gemini and return (plate_text, status)."""
    img_bytes = Path(img_path).read_bytes()
    ext = Path(img_path).suffix.lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    b64 = base64.b64encode(img_bytes).decode()

    print(f"       → Sending to Gemini [{MODEL}]...", end=" ", flush=True)

    for attempt in range(retry + 1):
        try:
            resp = model.generate_content([
                PROMPT,
                {"mime_type": mime, "data": b64}
            ])
            raw = resp.text.strip().upper()
            plate = "".join(c for c in raw if c.isalnum())
            print(f"Raw: '{raw}'")
            if plate and plate != "UNKNOWN":
                return plate, "SUCCESS"
            return "UNKNOWN", "NO_TEXT"
        except Exception as e:
            err = str(e)
            print(f"ERROR: {err[:150]}")
            if "quota" in err.lower() or "429" in err:
                wait = 15 * (attempt + 1)
                print(f"       ⏳ Rate limited — waiting {wait}s...")
                time.sleep(wait)
            elif attempt < retry:
                print(f"       🔁 Retrying ({attempt + 2}/{retry + 1})...")
                time.sleep(3)
            else:
                return "ERROR", err[:120]

def run(target: str, api_key: str, out_csv: str, delay: float):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL)

    if os.path.isfile(target):
        paths = [target]
    elif os.path.isdir(target):
        paths = sorted(
            glob.glob(os.path.join(target, "*.jpg")) +
            glob.glob(os.path.join(target, "*.jpeg")) +
            glob.glob(os.path.join(target, "*.png"))
        )
    else:
        print(f"[ERROR] Path not found: {target}"); sys.exit(1)

    if not paths:
        print(f"[WARNING] No images found in: {target}"); return

    print(f"\n{'='*65}")
    print(f"  🤖  Model  : {MODEL}")
    print(f"  📁  Source : {target}")
    print(f"  🖼️   Images : {len(paths)}")
    print(f"{'='*65}\n")

    rows, ok = [], 0
    for i, p in enumerate(paths, 1):
        fname = os.path.basename(p)
        plate, status = read_plate(model, p)

        if status == "SUCCESS":
            ok += 1; icon = "✅"
        elif status == "NO_TEXT":
            icon = "⚠️ "
        else:
            icon = "❌"

        print(f"[{i:03d}/{len(paths)}] {icon}  {fname:<32}  →  {plate}\n")
        rows.append([fname, plate, status, p])

        if delay > 0 and i < len(paths):
            time.sleep(delay)

    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "plate", "status", "path"])
        w.writerows(rows)

    print(f"\n{'='*65}")
    print(f"  ✅  Recognized : {ok} / {len(paths)}")
    print(f"  ❌  Unread     : {len(paths) - ok}")
    print(f"  💾  CSV saved  : {out_csv}")
    print(f"{'='*65}\n")

def main():
    p = argparse.ArgumentParser(description="Gemini Vision License Plate Recognition")
    p.add_argument("target", nargs="?", default="./outputs/crops/plates")
    p.add_argument("--key", default="", help="Gemini API key (or set GEMINI_API_KEY env var)")
    p.add_argument("--output_csv", default="./outputs/gemini_plates.csv")
    p.add_argument("--delay", type=float, default=13.0,
                   help="Seconds between API calls (default: 13s → safe under 5 RPM free tier). Lower on paid tier.")
    args = p.parse_args()
    run(args.target, load_key(args.key), args.output_csv, args.delay)

if __name__ == "__main__":
    main()
