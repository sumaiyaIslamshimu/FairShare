"""Runs the store scrapers one by one (each in isolation) and saves the results.

CLI (run from the backend/ folder):
    python -m app.scrapers.runner --store all
    python -m app.scrapers.runner --store daraz --query rice --query headphones
M4's admin "Refresh" button calls refresh_store(db, store) / refresh_all(db).
"""
import argparse

from app.scrapers import all_stores, get_scraper
from app.scrapers.base import HttpxFetcher, RobotsChecker
from app.scrapers.normalizer import InvalidProduct, normalize_product
from app.scrapers.persistence import mark_store_stale, record_run, save_normalized
from app.services.time_utils import utcnow

DEFAULT_QUERIES = ["rice", "headphones", "notebook"]


def combine_status(statuses: list, invalid: int) -> str:
    if not statuses:
        return "failure"
    if all(s == "unsupported" for s in statuses):
        return "unsupported"
    ok = [s for s in statuses if s in ("success", "partial")]
    if not ok:
        return "failure"
    if len(ok) == len(statuses) and all(s == "success" for s in ok) and invalid == 0:
        return "success"
    return "partial"


def refresh_store(db, store, queries=None, fetcher=None, limit=20, scraper=None, now=None) -> dict:
    """Never raises: every problem becomes a status for THIS store only."""
    started = now or utcnow()
    statuses, errors, notes = [], [], []
    saved = {"inserted": 0, "updated": 0, "price_changes": 0, "duplicates_in_run": 0, "needs_review": 0}
    items_found = invalid = 0
    robots_allowed = None
    try:
        scraper = scraper or get_scraper(store)
        fetcher = fetcher or HttpxFetcher()
        robots = RobotsChecker(fetcher)
        for query in (queries or DEFAULT_QUERIES):
            res = scraper.run(query, fetcher, robots=robots, limit=limit)
            statuses.append(res.status.value)
            items_found += res.items_found
            errors += [f"{query}: {e}" for e in res.errors]
            notes += [n for n in res.notes if n not in notes]
            if res.robots_allowed is not None:
                robots_allowed = res.robots_allowed if robots_allowed is None else (robots_allowed and res.robots_allowed)
            normalized = []
            for raw in res.products:
                try:
                    normalized.append(normalize_product(raw, scraper.base_url, started))
                except InvalidProduct as exc:
                    invalid += 1
                    errors.append(f"{query}: skipped item ({exc.reason})")
            for k, v in save_normalized(db, normalized, started).items():
                saved[k] += v
            if res.status.value == "unsupported":
                break  # no point repeating more queries
    except Exception as exc:  # one broken store must never stop the others
        statuses.append("failure")
        errors.append(f"runner error: {type(exc).__name__}")
    status = combine_status(statuses, invalid)
    finished = now or utcnow()
    if status in ("failure", "unsupported"):
        mark_store_stale(db, store)
    errors = errors[:20]
    record_run(db, store, status, started, finished, items_found, errors, notes, robots_allowed)
    return {"store": store, "status": status, "items_found": items_found, "saved": saved,
            "invalid_items": invalid, "errors": errors, "notes": notes, "robots_allowed": robots_allowed,
            "started_at": started, "finished_at": finished}


def refresh_all(db, stores=None, queries=None, fetcher=None, limit=20, scrapers=None) -> list:
    fetcher = fetcher or HttpxFetcher()   # one fetcher = one shared polite rate limit
    results = []
    for store in (stores or all_stores()):
        try:
            results.append(refresh_store(db, store, queries, fetcher, limit, (scrapers or {}).get(store)))
        except Exception as exc:
            results.append({"store": store, "status": "failure", "errors": [f"runner error: {type(exc).__name__}"]})
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="Refresh external store data.")
    ap.add_argument("--store", default="all", help="all | " + " | ".join(all_stores()))
    ap.add_argument("--query", action="append", help="search term (repeatable)")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()
    if args.store != "all" and args.store not in all_stores():
        raise SystemExit(f"Unknown store '{args.store}'. Choose: all, {', '.join(all_stores())}")

    from app.db.indexes import ensure_indexes
    from app.db.mongo import get_db
    db = get_db()
    ensure_indexes(db)
    stores = all_stores() if args.store == "all" else [args.store]
    for r in refresh_all(db, stores, args.query, limit=args.limit):
        print(f"{r['store']:<10} {r['status']:<12} items={r.get('items_found', 0)} saved={r.get('saved')}")
        for e in (r.get("errors") or [])[:3]:
            print(f"    error: {e}")
        for n in (r.get("notes") or [])[:2]:
            print(f"    note: {n}")


if __name__ == "__main__":
    main()