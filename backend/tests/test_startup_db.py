def test_health_reports_database_up(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "up"}


def test_swagger_docs_available(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_unknown_route_uses_standard_error_format(client):
    r = client.get("/api/nope")
    assert r.status_code == 404
    assert "error" in r.json() and "code" in r.json()["error"]


def test_indexes_make_email_unique(client, db):
    names = [i["name"] for i in db.users.list_indexes()]
    assert any("email" in n for n in names)