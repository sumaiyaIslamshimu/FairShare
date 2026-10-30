"""One-off diagnostic: why does the project's Python fetcher time out on Chaldal while curl works?

Run from the backend folder (with .venv active):   python diag_chaldal.py
It sends exactly 3 requests (3 seconds apart), always with the honest FairShareBot User-Agent.
Only the standard content-negotiation headers (Accept / Accept-Encoding) differ between the runs.
"""
import time

import httpx

UA = "FairShareBot/0.1 (university project; price comparison; respects robots.txt)"
URL = "https://chaldal.com/search/rice"
VARIANTS = {
    "A as the project sends it":        {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"},
    "B Accept */*":                     {"User-Agent": UA, "Accept": "*/*"},
    "C Accept */* and no compression":  {"User-Agent": UA, "Accept": "*/*", "Accept-Encoding": "identity"},
}

for name, headers in VARIANTS.items():
    start = time.monotonic()
    try:
        r = httpx.get(URL, headers=headers, timeout=httpx.Timeout(40.0, connect=10.0), follow_redirects=True)
        print(f"{name}: status={r.status_code} time={time.monotonic() - start:.1f}s "
              f"size={len(r.content)} bytes content-encoding={r.headers.get('content-encoding')}")
    except Exception as e:  # report whatever happened, do not retry
        print(f"{name}: {type(e).__name__} after {time.monotonic() - start:.1f}s")
    time.sleep(3)
