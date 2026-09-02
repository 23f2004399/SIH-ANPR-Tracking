#!/usr/bin/env python3
"""
Push videos into Supabase Storage
==================================
Uploads the full camera feed(s) and the per-vehicle clips, then prints the
public base URLs to feed back into upload_to_supabase.py and index.html.

    export SUPABASE_URL=https://<project>.supabase.co
    export SUPABASE_SERVICE_KEY=sb_secret_...
    python upload_videos.py                    # cam1 + all clips
    python upload_videos.py --all_cams         # all three full feeds too
    python upload_videos.py --dry_run

Create the bucket first in the dashboard (Storage -> New bucket -> name it
"videos" -> tick Public), otherwise every upload returns 404 Bucket not found.
"""

import os
import sys
import glob
import argparse

try:
    import requests
except ImportError:
    sys.exit("[ERROR] pip install requests")

CONTENT_TYPES = {".mp4": "video/mp4", ".json": "application/json"}


def auth_headers(key):
    """Storage needs BOTH headers. With only Authorization it tries to parse the
    key as a JWT, and the new sb_secret_... format is not one — hence
    'Invalid Compact JWS'. The apikey header is what identifies the project."""
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def preflight(url, key, bucket):
    """Check auth and bucket before pushing 90MB and failing on every file."""
    try:
        r = requests.get(f"{url}/storage/v1/bucket/{bucket}",
                         headers=auth_headers(key), timeout=30)
    except requests.RequestException as exc:
        sys.exit(f"[ERROR] Cannot reach {url}: {exc}")

    if r.status_code == 200:
        info = r.json()
        if not info.get("public"):
            print(f"[WARN] Bucket '{bucket}' is PRIVATE — uploads will succeed but "
                  f"the videos will not load in the browser.\n"
                  f"       Storage -> {bucket} -> Settings -> make it public.\n")
        return
    if r.status_code == 404:
        sys.exit(f"[ERROR] Bucket '{bucket}' does not exist.\n"
                 f"        Storage -> New bucket -> name it '{bucket}' -> tick Public.")
    if r.status_code in (401, 403):
        sys.exit(f"[ERROR] Key rejected ({r.status_code}): {r.text[:200]}\n\n"
                 f"        Check SUPABASE_SERVICE_KEY is the SECRET key.\n"
                 f"        If it still fails, this project may need the legacy JWT key:\n"
                 f"        Settings -> API Keys -> 'Legacy anon, service_role API keys'\n"
                 f"        tab -> copy service_role (starts with eyJ...).")
    sys.exit(f"[ERROR] Unexpected {r.status_code}: {r.text[:200]}")


def upload(url, key, bucket, remote_path, local_path, dry_run):
    endpoint = f"{url}/storage/v1/object/{bucket}/{remote_path}"
    ctype = CONTENT_TYPES.get(os.path.splitext(local_path)[1].lower(),
                              "application/octet-stream")
    size_mb = os.path.getsize(local_path) / 1e6
    if dry_run:
        print(f"    would upload {local_path}  ->  {bucket}/{remote_path}  ({size_mb:.1f} MB)")
        return True

    print(f"    {remote_path:<34} {size_mb:6.1f} MB ", end="", flush=True)
    with open(local_path, "rb") as fh:
        resp = requests.post(
            endpoint, data=fh,
            headers={
                **auth_headers(key),
                "Content-Type": ctype,
                # Overwrite instead of failing when re-running the script.
                "x-upsert": "true",
            },
            timeout=600,
        )
    if resp.status_code in (200, 201):
        print("ok")
        return True
    print(f"FAILED {resp.status_code}: {resp.text[:160]}")
    return False


def main():
    ap = argparse.ArgumentParser(description="Upload videos to Supabase Storage")
    ap.add_argument("--bucket", default="videos")
    ap.add_argument("--videos_dir", default="./web_videos")
    ap.add_argument("--clips_dir", default="./clips")
    ap.add_argument("--all_cams", action="store_true",
                    help="Upload cam2/cam3 as well (only cam1 is used as the live feed)")
    ap.add_argument("--skip_clips", action="store_true")
    ap.add_argument("--dry_run", action="store_true")
    args = ap.parse_args()

    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not args.dry_run and not (url and key):
        sys.exit("[ERROR] Set SUPABASE_URL and SUPABASE_SERVICE_KEY first.")

    jobs = []
    cams = ["cam1.mp4", "cam2.mp4", "cam3.mp4"] if args.all_cams else ["cam1.mp4"]
    for name in cams:
        path = os.path.join(args.videos_dir, name)
        if os.path.isfile(path):
            jobs.append((f"feeds/{name}", path))
        else:
            print(f"[WARN] missing {path}")

    if not args.skip_clips:
        for path in sorted(glob.glob(os.path.join(args.clips_dir, "*.mp4"))):
            jobs.append((f"clips/{os.path.basename(path)}", path))

    if not jobs:
        sys.exit("[ERROR] Nothing to upload.")

    total_mb = sum(os.path.getsize(p) for _, p in jobs) / 1e6
    print(f"\n  bucket : {args.bucket}")
    print(f"  files  : {len(jobs)}  ({total_mb:.1f} MB)\n")

    if not args.dry_run:
        preflight(url, key, args.bucket)

    ok = sum(upload(url, key, args.bucket, remote, local, args.dry_run)
             for remote, local in jobs)

    print(f"\n  uploaded {ok}/{len(jobs)}")
    if args.dry_run:
        return

    base = f"{url}/storage/v1/object/public/{args.bucket}"
    print(f"\n{'='*74}")
    print("  Put these into the next two steps:\n")
    print(f"  1) python upload_to_supabase.py --video_base {base}/feeds\n")
    print(f"  2) in index.html CONFIG, set:")
    print(f"       CLIPS_DIR: '{base}/clips',")
    print(f"{'='*74}\n")


if __name__ == "__main__":
    main()
