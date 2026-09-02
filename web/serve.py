#!/usr/bin/env python3
"""
Range-capable static server for the ANPR dashboard
===================================================
    python serve.py              # http://127.0.0.1:8000
    python serve.py 9000

Python's builtin `http.server` answers every request with 200 and the whole
file — it does not implement HTTP Range. Browsers need 206 Partial Content to
seek inside a video, so with the builtin server `video.currentTime = 27.2`
either stalls or forces a full download first. This adds Range support so the
two-camera playback jumps straight to the right moment.
"""

import os
import re
import sys
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


class RangeHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_head(self):
        header = self.headers.get("Range")
        if not header:
            return super().send_head()

        path = self.translate_path(self.path)
        if os.path.isdir(path) or not os.path.isfile(path):
            return super().send_head()

        match = RANGE_RE.match(header.strip())
        if not match:
            return super().send_head()

        size = os.path.getsize(path)
        start_s, end_s = match.groups()
        if start_s:
            start = int(start_s)
            end = int(end_s) if end_s else size - 1
        else:                                   # suffix form: "bytes=-500"
            if not end_s:
                return super().send_head()
            start = max(0, size - int(end_s))
            end = size - 1
        end = min(end, size - 1)

        if start >= size or start > end:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None

        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        # copyfile() would stream to EOF; cap it at the requested slice.
        return _Slice(f, end - start + 1)


class _Slice:
    """File wrapper that stops after n bytes, so copyfile honours the range."""

    def __init__(self, fh, remaining):
        self.fh, self.remaining = fh, remaining

    def read(self, amount=-1):
        if self.remaining <= 0:
            return b""
        if amount < 0 or amount > self.remaining:
            amount = self.remaining
        chunk = self.fh.read(amount)
        self.remaining -= len(chunk)
        return chunk

    def close(self):
        self.fh.close()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    root = os.path.dirname(os.path.abspath(__file__))
    handler = functools.partial(RangeHandler, directory=root)

    print(f"\n  ANPR dashboard  ->  http://127.0.0.1:{port}/index.html")
    print(f"  serving         :  {root}")
    print(f"  range requests  :  enabled (video seeking works)\n")
    try:
        ThreadingHTTPServer(("0.0.0.0", port), handler).serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped.\n")


if __name__ == "__main__":
    main()
