"""
Backend tests for PSICOLFIS sectors feature + regression on core endpoints.
Covers:
 - GET /api/sectors (list of 3 sectors, no deployment_id in list)
 - GET /api/sectors/{slug} for each of the 3 valid slugs (includes deployment_id)
 - GET /api/sectors/inexistente -> 404
 - Regression: /api/ (root), /api/reviews, /api/captcha, /api/admin/login
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback: read from frontend .env since backend container uses same preview URL
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                    break
    except Exception:
        pass

ADMIN_EMAIL = "obdulio@psicolfis.net"
ADMIN_PASSWORD = "Clau49006@."

EXPECTED_SLUGS = {"inmobiliarias", "clinicas-dentales", "salones-belleza"}


@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ------------------- Sectors: list -------------------

class TestSectorsList:
    def test_list_returns_three_items(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/sectors", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "items" in data and "total" in data
        assert data["total"] == 3
        assert isinstance(data["items"], list) and len(data["items"]) == 3

    def test_list_has_expected_slugs(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/sectors", timeout=20)
        slugs = {item["slug"] for item in r.json()["items"]}
        assert slugs == EXPECTED_SLUGS

    def test_list_does_not_expose_deployment(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/sectors", timeout=20)
        for item in r.json()["items"]:
            assert "deployment_id" not in item, f"Listing should not expose deployment_id: {item}"
            assert "deployment_env" not in item
            # Must still have public fields
            for k in ("name", "tagline", "headline", "metrics", "use_cases"):
                assert k in item, f"missing '{k}' in sector listing"


# ------------------- Sectors: detail -------------------

@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS))
class TestSectorDetail:
    def test_detail_ok(self, api_client, slug):
        r = api_client.get(f"{BASE_URL}/api/sectors/{slug}", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["slug"] == slug
        # Must contain deployment_id key (empty string expected until configured)
        assert "deployment_id" in data, "detail must include deployment_id key"
        assert isinstance(data["deployment_id"], str)
        # Must NOT expose internal env var name
        assert "deployment_env" not in data
        # Public fields
        for k in ("headline", "problem", "solution", "use_cases", "metrics", "demo_intro"):
            assert k in data, f"missing '{k}' in sector detail"
        assert isinstance(data["use_cases"], list) and len(data["use_cases"]) == 5
        assert isinstance(data["metrics"], list) and len(data["metrics"]) == 3

    def test_detail_deployment_empty_when_env_unset(self, api_client, slug):
        r = api_client.get(f"{BASE_URL}/api/sectors/{slug}", timeout=20)
        data = r.json()
        # Per current .env, all three PICKAXE_DEPLOYMENT_SECTOR_* are empty strings
        assert data["deployment_id"] == "", f"Expected empty deployment_id for {slug}, got '{data['deployment_id']}'"


class TestSectorDetailNotFound:
    def test_404_on_unknown_slug(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/sectors/agente-inexistente", timeout=20)
        assert r.status_code == 404
        data = r.json()
        assert data.get("detail") == "Sector no encontrado"


# ------------------- Regression -------------------

class TestRegression:
    def test_root(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/", timeout=20)
        assert r.status_code == 200
        assert r.json().get("message") == "Hello World"

    def test_reviews(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/reviews", timeout=20)
        assert r.status_code == 200
        data = r.json()
        # Should be a list or dict with items
        if isinstance(data, dict):
            assert "items" in data or "reviews" in data or "total" in data
        else:
            assert isinstance(data, list)

    def test_captcha(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/captcha", timeout=20)
        assert r.status_code == 200
        data = r.json()
        # Captcha must issue some challenge id/payload
        assert isinstance(data, dict) and len(data) > 0

    def test_admin_login_ok(self, api_client):
        r = api_client.post(
            f"{BASE_URL}/api/admin/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # Token could be in body or in httpOnly cookie; accept either
        has_token = ("token" in data) or ("access_token" in data) or any(
            "admin" in k.lower() or "token" in k.lower() for k in r.cookies.keys()
        )
        assert has_token, f"Expected token in body or cookie, got body={data}, cookies={r.cookies.keys()}"

    def test_admin_login_bad_creds(self, api_client):
        r = api_client.post(
            f"{BASE_URL}/api/admin/login",
            json={"email": ADMIN_EMAIL, "password": "wrongpass-xyz"},
            timeout=20,
        )
        assert r.status_code in (401, 403, 429), r.text
