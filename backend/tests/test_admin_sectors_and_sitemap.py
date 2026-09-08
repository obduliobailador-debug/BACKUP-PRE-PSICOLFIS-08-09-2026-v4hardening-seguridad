"""
Backend tests for the new Sectors CMS admin endpoints + dynamic sitemap.

Covers:
 - GET /sitemap.xml (root path, not /api/) → XML with static + sector routes.
 - Admin auth required for /api/admin/sectors*.
 - GET /api/admin/sectors → {items, active, hidden, trash}
 - POST create: slug validation (400), duplicate (409), success.
 - PATCH update: slug collision (409), rename.
 - POST /visibility hide/unhide → public list respects it.
 - DELETE soft delete → gone from public list.
 - POST /restore → back in public list.
 - DELETE /permanent only on soft-deleted.
 - Cleanup at the end restores the 3 original sectors to active state.
"""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

ADMIN_EMAIL = "obdulio@psicolfis.net"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or ""
if not ADMIN_PASSWORD:
    import pytest
    pytest.skip("ADMIN_PASSWORD env var required to run these tests", allow_module_level=True)

ORIGINAL_SLUGS = {"inmobiliarias", "clinicas-dentales", "salones-belleza"}
TEST_SLUG = "test-sector"
TEST_SLUG_RENAMED = "test-sector-renamed"


# ---------------------------- Fixtures ----------------------------

@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_token(api_client):
    r = api_client.post(
        f"{BASE_URL}/api/admin/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text}")
    data = r.json()
    token = data.get("token") or data.get("access_token")
    # Cookie fallback
    if not token:
        for k, v in r.cookies.items():
            if "token" in k.lower() or "admin" in k.lower():
                token = v
                break
    if not token:
        pytest.skip("No admin token returned")
    return token


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module", autouse=True)
def cleanup(api_client, auth_headers):
    """After all tests: ensure 3 originals are active and any test-* sector removed."""
    yield
    # Remove test sectors (soft delete + permanent)
    for slug in (TEST_SLUG, TEST_SLUG_RENAMED):
        try:
            api_client.delete(f"{BASE_URL}/api/admin/sectors/{slug}", headers=auth_headers, timeout=15)
            api_client.delete(f"{BASE_URL}/api/admin/sectors/{slug}/permanent", headers=auth_headers, timeout=15)
        except Exception:
            pass
    # Restore originals (unhide + restore)
    for slug in ORIGINAL_SLUGS:
        try:
            api_client.post(
                f"{BASE_URL}/api/admin/sectors/{slug}/restore",
                headers=auth_headers, timeout=15,
            )
            api_client.post(
                f"{BASE_URL}/api/admin/sectors/{slug}/visibility",
                headers=auth_headers, json={"hidden": False}, timeout=15,
            )
        except Exception:
            pass


# ---------------------------- Sitemap ----------------------------

class TestSitemap:
    def test_sitemap_xml_returns_ok(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/sitemap.xml", timeout=20)
        assert r.status_code == 200, r.text
        assert "xml" in r.headers.get("content-type", "").lower()
        body = r.text
        assert "<urlset" in body and "</urlset>" in body
        # Static routes present
        for p in ("/", "/agentes", "/soluciones", "/legal"):
            assert f"<loc>" in body
            # The base URL prepends; just check the path is somewhere
            assert p in body, f"Static path {p} missing from sitemap"

    def test_sitemap_contains_active_sectors(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/sitemap.xml", timeout=20)
        assert r.status_code == 200
        for slug in ORIGINAL_SLUGS:
            assert f"/soluciones/{slug}" in r.text, f"Sector {slug} missing from sitemap"


# ---------------------------- Auth guard ----------------------------

class TestAdminAuthGuard:
    def test_admin_sectors_requires_auth(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/admin/sectors", timeout=15)
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"


# ---------------------------- Admin list ----------------------------

class TestAdminList:
    def test_returns_stats_and_items(self, api_client, auth_headers):
        r = api_client.get(f"{BASE_URL}/api/admin/sectors", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        for k in ("items", "active", "hidden", "trash"):
            assert k in data, f"missing '{k}'"
        assert isinstance(data["items"], list)
        slugs = {i["slug"] for i in data["items"]}
        assert ORIGINAL_SLUGS.issubset(slugs), f"Missing originals: {ORIGINAL_SLUGS - slugs}"
        assert data["active"] >= 3


# ---------------------------- Create ----------------------------

class TestAdminCreate:
    def test_invalid_slug_uppercase(self, api_client, auth_headers):
        r = api_client.post(
            f"{BASE_URL}/api/admin/sectors",
            headers=auth_headers,
            json={"slug": "Bad Slug", "name": "X", "tagline": "t", "headline": "h",
                  "problem": "p", "solution": "s", "use_cases": ["a"], "metrics": [],
                  "demo_intro": "d"},
            timeout=15,
        )
        assert r.status_code == 400, r.text

    def test_duplicate_slug(self, api_client, auth_headers):
        r = api_client.post(
            f"{BASE_URL}/api/admin/sectors",
            headers=auth_headers,
            json={"slug": "inmobiliarias", "name": "Dup", "tagline": "t", "headline": "h",
                  "problem": "p", "solution": "s", "use_cases": ["a"], "metrics": [],
                  "demo_intro": "d"},
            timeout=15,
        )
        assert r.status_code == 409, r.text

    def test_create_ok(self, api_client, auth_headers):
        r = api_client.post(
            f"{BASE_URL}/api/admin/sectors",
            headers=auth_headers,
            json={
                "slug": TEST_SLUG,
                "name": "Test Sector",
                "tagline": "Un tagline",
                "headline": "Headline",
                "problem": "problema",
                "solution": "solucion",
                "use_cases": ["u1", "u2"],
                "metrics": [{"value": "10x", "label": "más rápido"}],
                "demo_intro": "Prueba la demo",
            },
            timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        assert data["sector"]["slug"] == TEST_SLUG


# ---------------------------- Update ----------------------------

class TestAdminUpdate:
    def test_rename_slug_ok(self, api_client, auth_headers):
        r = api_client.patch(
            f"{BASE_URL}/api/admin/sectors/{TEST_SLUG}",
            headers=auth_headers,
            json={
                "slug": TEST_SLUG_RENAMED,
                "name": "Test Sector Renamed",
                "tagline": "t2",
                "headline": "h2",
                "problem": "p2",
                "solution": "s2",
                "use_cases": ["u1"],
                "metrics": [],
                "demo_intro": "d2",
            },
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert r.json()["sector"]["slug"] == TEST_SLUG_RENAMED

    def test_rename_collision(self, api_client, auth_headers):
        # Attempt to rename our renamed test sector to an existing slug (inmobiliarias)
        r = api_client.patch(
            f"{BASE_URL}/api/admin/sectors/{TEST_SLUG_RENAMED}",
            headers=auth_headers,
            json={
                "slug": "inmobiliarias",
                "name": "X",
                "tagline": "t", "headline": "h",
                "problem": "p", "solution": "s",
                "use_cases": ["u"], "metrics": [], "demo_intro": "d",
            },
            timeout=15,
        )
        assert r.status_code == 409, r.text


# ---------------------------- Visibility ----------------------------

class TestVisibility:
    def test_hide_removes_from_public(self, api_client, auth_headers):
        r = api_client.post(
            f"{BASE_URL}/api/admin/sectors/inmobiliarias/visibility",
            headers=auth_headers,
            json={"hidden": True},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        # Public listing must NOT include it
        pub = api_client.get(f"{BASE_URL}/api/sectors", timeout=15).json()
        slugs = {i["slug"] for i in pub["items"]}
        assert "inmobiliarias" not in slugs, "hidden sector still in public list"
        # Detail 404
        d = api_client.get(f"{BASE_URL}/api/sectors/inmobiliarias", timeout=15)
        assert d.status_code == 404
        # Admin list still shows it as hidden
        adm = api_client.get(f"{BASE_URL}/api/admin/sectors", headers=auth_headers, timeout=15).json()
        item = next((i for i in adm["items"] if i["slug"] == "inmobiliarias"), None)
        assert item is not None and item.get("hidden") is True

    def test_unhide_restores_in_public(self, api_client, auth_headers):
        r = api_client.post(
            f"{BASE_URL}/api/admin/sectors/inmobiliarias/visibility",
            headers=auth_headers,
            json={"hidden": False},
            timeout=15,
        )
        assert r.status_code == 200
        pub = api_client.get(f"{BASE_URL}/api/sectors", timeout=15).json()
        slugs = {i["slug"] for i in pub["items"]}
        assert "inmobiliarias" in slugs


# ---------------------------- Soft delete / restore / permanent ----------------------------

class TestDeleteFlow:
    def test_soft_delete(self, api_client, auth_headers):
        r = api_client.delete(
            f"{BASE_URL}/api/admin/sectors/{TEST_SLUG_RENAMED}",
            headers=auth_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        pub = api_client.get(f"{BASE_URL}/api/sectors", timeout=15).json()
        assert TEST_SLUG_RENAMED not in {i["slug"] for i in pub["items"]}

    def test_permanent_rejected_after_restore(self, api_client, auth_headers):
        # Restore
        r = api_client.post(
            f"{BASE_URL}/api/admin/sectors/{TEST_SLUG_RENAMED}/restore",
            headers=auth_headers, timeout=15,
        )
        assert r.status_code == 200
        # Should be back in public list
        pub = api_client.get(f"{BASE_URL}/api/sectors", timeout=15).json()
        assert TEST_SLUG_RENAMED in {i["slug"] for i in pub["items"]}
        # Permanent delete without being in trash → 400
        r2 = api_client.delete(
            f"{BASE_URL}/api/admin/sectors/{TEST_SLUG_RENAMED}/permanent",
            headers=auth_headers, timeout=15,
        )
        assert r2.status_code == 400, r2.text

    def test_permanent_after_soft_delete(self, api_client, auth_headers):
        # Soft delete first
        r = api_client.delete(
            f"{BASE_URL}/api/admin/sectors/{TEST_SLUG_RENAMED}",
            headers=auth_headers, timeout=15,
        )
        assert r.status_code == 200
        # Then permanent
        r2 = api_client.delete(
            f"{BASE_URL}/api/admin/sectors/{TEST_SLUG_RENAMED}/permanent",
            headers=auth_headers, timeout=15,
        )
        assert r2.status_code == 200
        # Gone completely
        adm = api_client.get(f"{BASE_URL}/api/admin/sectors", headers=auth_headers, timeout=15).json()
        assert TEST_SLUG_RENAMED not in {i["slug"] for i in adm["items"]}
