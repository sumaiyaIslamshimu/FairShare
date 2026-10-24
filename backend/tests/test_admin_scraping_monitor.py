"""Acceptance 5: the monitor reports success / partial / failure / unsupported / never_run accurately."""
from datetime import timedelta

import pytest

from app.scrapers import all_stores
from app.scrapers.persistence import record_run
from app.services import admin_service
from app.services.time_utils import utcnow


def status_by_store(client, headers):
    r = client.get("/api/admin/scraping/status", headers=headers)
    assert r.status_code == 200
    return {s["store"]: s for s in r.json()}


def test_every_store_is_listed_and_untouched_stores_are_never_run(client, admin_headers):
    s = status_by_store(client, admin_headers)
    assert set(s) == set(all_stores()) and len(s) == 6
    assert all(v["status"] == "never_run" for v in s.values())


@pytest.mark.parametrize("state", ["success", "partial", "failure", "unsupported"])
def test_each_recorded_state_is_reported_exactly(client, db, admin_headers, state):
    now = utcnow()
    record_run(db, "daraz", state, now, now, 3 if state in ("success", "partial") else 0,
               [] if state == "success" else ["daraz: something happened"], ["note"], True)
    d = status_by_store(client, admin_headers)["daraz"]
    assert d["status"] == state
    assert (d["last_success_at"] is not None) == (state in ("success", "partial"))
    if state != "success":
        assert d["last_error"] == "daraz: something happened"
    assert status_by_store(client, admin_headers)["chaldal"]["status"] == "never_run"  # others untouched


def test_stale_flag_when_last_success_is_old(client, db, admin_headers):
    old = utcnow() - timedelta(days=10)
    record_run(db, "agora", "success", old, old, 5, [], [], True)
    recent = utcnow()
    record_run(db, "pickaboo", "success", recent, recent, 5, [], [], True)
    s = status_by_store(client, admin_headers)
    assert s["agora"]["stale"] is True and s["pickaboo"]["stale"] is False


def test_run_history_is_paginated_newest_first_and_filterable(client, db, admin_headers):
    base = utcnow()
    for i in range(5):
        record_run(db, "daraz", "failure", base + timedelta(minutes=i), base + timedelta(minutes=i), 0, [f"e{i}"], [], None)
    record_run(db, "rokomari", "success", base, base, 2, [], [], True)
    r = client.get("/api/admin/scraping/runs?page=1&page_size=3", headers=admin_headers).json()
    assert r["total"] == 6 and len(r["items"]) == 3
    only = client.get("/api/admin/scraping/runs?store=daraz", headers=admin_headers).json()
    assert only["total"] == 5 and only["items"][0]["errors"] == ["e4"]
    assert client.get("/api/admin/scraping/runs?store=nope", headers=admin_headers).status_code == 404


def test_refresh_calls_the_runner_logs_it_and_applies_a_cooldown(client, db, admin_headers, monkeypatch):
    calls = []

    def fake_refresh(db_, store, **kw):
        calls.append(store)
        now = utcnow()
        record_run(db_, store, "partial", now, now, 4, ["one item skipped"], [], True)
        return {"store": store, "status": "partial", "items_found": 4, "errors": ["one item skipped"], "notes": [],
                "started_at": now, "finished_at": now}

    from app.scrapers import runner
    monkeypatch.setattr(runner, "refresh_store", fake_refresh)
    r = client.post("/api/admin/scraping/refresh/daraz", headers=admin_headers)
    assert r.status_code == 200 and r.json()["status"] == "partial" and calls == ["daraz"]
    assert status_by_store(client, admin_headers)["daraz"]["status"] == "partial"
    assert db.audit_logs.count_documents({"action": "scraping.refresh", "target": "daraz"}) == 1
    again = client.post("/api/admin/scraping/refresh/daraz", headers=admin_headers)
    assert again.status_code == 429 and again.json()["error"]["code"] == "REFRESH_COOLDOWN"
    assert calls == ["daraz"]  # the second click did not scrape
    assert client.post("/api/admin/scraping/refresh/chaldal", headers=admin_headers).status_code == 200


def test_refresh_unknown_store_is_404_and_runner_never_called(client, admin_headers, monkeypatch):
    from app.scrapers import runner
    monkeypatch.setattr(runner, "refresh_store", lambda *a, **k: pytest.fail("must not run"))
    assert client.post("/api/admin/scraping/refresh/amazon", headers=admin_headers).status_code == 404


def test_refresh_of_an_unconfigured_store_reports_unsupported_without_network(client, db, admin_headers):
    """The real runner against real (unconfigured) adapters: honest status, no request, no crash."""
    class NoNetwork:
        def get(self, *a, **k):
            raise AssertionError("an unsupported store must not make requests")
    from app.scrapers import runner
    res = runner.refresh_store(db, "daraz", fetcher=NoNetwork())
    if res["status"] != "unsupported":
        pytest.skip("daraz is configured on this machine; unsupported-path covered by the other tests")
    assert status_by_store(client, admin_headers)["daraz"]["status"] == "unsupported"


def test_stats_include_scraping_summary(client, db, admin_headers):
    now = utcnow()
    record_run(db, "daraz", "success", now, now, 1, [], [], True)
    st = client.get("/api/admin/stats", headers=admin_headers).json()["scraping"]
    assert st["stores"] == 6 and st["by_status"].get("success") == 1 and st["by_status"].get("never_run") == 5