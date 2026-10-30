"""Read-only reconnaissance for ONE public page. Run it yourself, on your own machine/network:

    python -m app.scrapers.recon "https://example.com/some/public/listing/page"
    python -m app.scrapers.recon "<url>" --save daraz     # also saves a cleaned copy as a test fixture

What it does: checks robots.txt, fetches the page once (polite, honest User-Agent), and reports what kind of
data the page offers (JSON-LD products, embedded JSON, plain HTML). It does NOT bypass anything: a 403/429
or a robots.txt disallow is reported as-is and the page is not fetched again.
--save stores the page WITHOUT <script> tags (except JSON-LD) so tokens/cookies are not kept in fixtures.
Paste the printed report (it contains no secrets) back to your assistant so the real adapter can be written.
"""
import argparse
import re
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup

from app.scrapers.base import FetchError, HttpxFetcher, RobotsChecker, extract_jsonld_products

MARKERS = ["__NEXT_DATA__", "__NUXT__", "window.__INITIAL_STATE__", "window.__PRELOADED_STATE__",
           "application/json", "dataLayer", "schema.org/Product"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--save", metavar="STORE", help="save cleaned HTML to tests/fixtures/<STORE>/recon_page.html")
    ap.add_argument("--timeout", type=float, default=10.0, help="Timeout in seconds for the fetch operation")
    args = ap.parse_args()

    # Pass the custom timeout and force 0 retries for recon
    fetcher = HttpxFetcher(min_interval=2.0, timeout=args.timeout, retries=0)
    robots = RobotsChecker(fetcher)
    print(f"URL: {args.url}")
    allowed = robots.allowed(args.url)
    print(f"robots.txt allows this fetch: {allowed}")
    if not allowed:
        print("STOP: not fetching. Record this as 'unsupported (robots.txt)' for this store.")
        return 0

    start_time = time.time()
    try:
        resp = fetcher.get(args.url)
        elapsed = time.time() - start_time
        print(f"FETCH SUCCESSFUL in {elapsed:.2f} seconds.")
    except FetchError as e:
        elapsed = time.time() - start_time
        print(f"FETCH FAILED after {elapsed:.2f} seconds: kind={e.kind} status={e.status_code} message={e}")
        print("Not retrying and not working around it. Record this exact result for the store.")
        return 0

    html = resp.text
    print(f"HTTP {resp.status_code}, content-type: {resp.content_type}, size: {len(html)} chars")
    print(f"JSON-LD Product objects: {len(extract_jsonld_products(html))}")
    for m in MARKERS:
        if m in html:
            print(f"marker present: {m}")
    soup = BeautifulSoup(html, "lxml")
    print(f"<a> links: {len(soup.find_all('a'))}, <img>: {len(soup.find_all('img'))}")
    tk_count = len(re.findall(r"Tk\.?\s*\d", html))
    print(f"mentions of currency symbols: ৳={html.count('৳')}, 'Tk'={tk_count}")
    if "captcha" in html.lower() or "access denied" in html.lower():
        print("WARNING: page text mentions captcha/access denied -> likely a block page, do not scrape.")

    if args.save:
        for s in soup.find_all("script"):
            if s.get("type") != "application/ld+json":
                s.decompose()
        out_dir = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / args.save
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "recon_page.html"
        out.write_text(str(soup), encoding="utf-8")
        print(f"saved cleaned copy: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())