"""Acceptance 7: every path the frontend calls exists in the backend's OpenAPI schema (with that HTTP method).

Reads frontend/src/api/*.js and looks at every request("...") and requestBlob("...") call. Template parts such as ${id} become {} and
query strings are ignored, so  `/admin/users/${id}`  must match  /api/admin/users/{user_id}.
"""
import re
from pathlib import Path

import pytest

from app.main import app

API_DIR = Path(__file__).resolve().parents[2] / "frontend" / "src" / "api"
CALL = re.compile(r"""request(?:Blob)?\(\s*(?P<q>[`"'])(?P<path>.*?)(?P=q)\s*(?:,\s*\{(?P<opts>[^{}]*(?:\{[^{}]*\}[^{}]*)*)\})?\s*\)""", re.S)
METHOD = re.compile(r"""method:\s*["'](\w+)["']""")


def normalize(path: str) -> str:
    path = re.sub(r"/\$\{[^}]*\}", "/{}", path)   # /${id} -> /{}
    path = re.sub(r"\$\{[^}]*\}", "", path)       # trailing ${qs} / ?page=${p}
    path = path.split("?")[0]
    return path.rstrip("/") or "/"


def frontend_calls():
    calls = []
    for f in sorted(API_DIR.glob("*.js")):
        for m in CALL.finditer(f.read_text(encoding="utf-8")):
            method = METHOD.search(m.group("opts") or "")
            calls.append((f.name, (method.group(1) if method else "GET").upper(), normalize(m.group("path"))))
    return calls


def backend_routes():
    routes = set()
    for path, methods in app.openapi()["paths"].items():
        norm = re.sub(r"\{[^}]+\}", "{}", path.removeprefix("/api")).rstrip("/") or "/"
        for method in methods:
            routes.add((method.upper(), norm))
    return routes


pytestmark = pytest.mark.skipif(not API_DIR.exists(), reason="frontend/src/api not found next to backend/")


def test_the_extractor_finds_calls_from_every_member():
    files = {c[0] for c in frontend_calls()}
    assert {"auth.js", "admin.js", "verification.js", "complaints.js"} <= files
    assert len(frontend_calls()) >= 40


def test_normalizer_handles_templates_and_queries():
    assert normalize("/admin/users/${id}") == "/admin/users/{}"
    assert normalize("/admin/users${qs(params)}") == "/admin/users"
    assert normalize("/seller/products?page=${page}") == "/seller/products"
    assert normalize("/seller/products/${id}/inventory") == "/seller/products/{}/inventory"


def test_every_frontend_api_call_exists_in_the_backend():
    known = backend_routes()
    missing = [f"{f}: {m} {p}" for f, m, p in frontend_calls() if (m, p) not in known]
    assert not missing, "Frontend calls with no matching backend route:\n  " + "\n  ".join(missing)


def test_member4_routes_are_all_called_by_the_frontend():
    """The other direction for Member 4's own area: an admin route nobody uses is dead code or a missing page."""
    called = {(m, p) for _, m, p in frontend_calls()}
    mine = {r for r in backend_routes()
            if r[1].startswith(("/admin", "/verification", "/complaints"))}
    unused = sorted(r for r in mine if r not in called)
    assert not unused, f"Member 4 routes with no frontend caller: {unused}"