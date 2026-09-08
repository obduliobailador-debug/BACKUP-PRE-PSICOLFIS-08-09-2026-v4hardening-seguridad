"""Backend tests for PSICOLFIS.NET admin panel - Regalar acceso (manual access links)
covers: admin login, admin/me, access-links CRUD + revoke + resend, /access/validate
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://repo-modify-zone.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "obdulio@psicolfis.net"
ADMIN_PASSWORD = "Clau49006@."

# Track ids created for cleanup
_created_link_ids = []
_created_jtis = []


@pytest.fixture(scope="session")
def http():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def admin_token(http):
    r = http.post(f"{API}/admin/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=60)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 20
    assert data.get("expires_in_hours") == 8
    return data["token"]


@pytest.fixture(scope="session")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ---------- Auth ----------

class TestAdminAuth:
    def test_login_invalid_credentials(self, http):
        r = http.post(f"{API}/admin/login", json={"email": "wrong@example.com", "password": "badpass123!"}, timeout=60)
        assert r.status_code == 401
        body = r.json()
        assert "detail" in body

    def test_login_success(self, admin_token):
        assert admin_token

    def test_admin_me_no_token(self, http):
        r = http.get(f"{API}/admin/me", timeout=60)
        assert r.status_code == 401

    def test_admin_me_invalid_token(self, http):
        r = http.get(f"{API}/admin/me", headers={"Authorization": "Bearer not.a.valid.jwt"}, timeout=60)
        assert r.status_code == 401

    def test_admin_me_valid(self, http, auth_headers):
        r = http.get(f"{API}/admin/me", headers=auth_headers, timeout=60)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == ADMIN_EMAIL.lower()
        assert data["role"] == "admin"
        assert isinstance(data["exp"], int)


# ---------- Existing endpoints (regression) ----------

class TestExistingEndpoints:
    def test_budget_requests_requires_auth(self, http):
        assert http.get(f"{API}/admin/budget-requests", timeout=60).status_code == 401

    def test_budget_requests_with_auth(self, http, auth_headers):
        r = http.get(f"{API}/admin/budget-requests", headers=auth_headers, timeout=60)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data and isinstance(data["items"], list)
        assert "unread" in data and "total" in data

    def test_reviews_requires_auth(self, http):
        assert http.get(f"{API}/admin/reviews", timeout=60).status_code == 401

    def test_reviews_with_auth(self, http, auth_headers):
        r = http.get(f"{API}/admin/reviews", headers=auth_headers, timeout=60)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data and isinstance(data["items"], list)


# ---------- Access Links: auth required ----------

class TestAccessLinksAuth:
    def test_list_requires_auth(self, http):
        assert http.get(f"{API}/admin/access-links", timeout=60).status_code == 401

    def test_create_requires_auth(self, http):
        r = http.post(f"{API}/admin/access-links", json={
            "customer_email": "TEST_unauth@example.com",
            "agent_id": "iris",
            "level": "demo",
            "send_email": False,
        }, timeout=60)
        assert r.status_code == 401

    def test_resend_requires_auth(self, http):
        assert http.post(f"{API}/admin/access-links/fake-id/resend", timeout=60).status_code == 401

    def test_revoke_requires_auth(self, http):
        assert http.post(f"{API}/admin/access-links/fake-id/revoke", timeout=60).status_code == 401

    def test_delete_requires_auth(self, http):
        assert http.delete(f"{API}/admin/access-links/fake-id", timeout=60).status_code == 401


# ---------- Access Links: create/list/validate/revoke/delete ----------

class TestAccessLinksFlow:
    def test_create_skipped_email(self, http, auth_headers):
        payload = {
            "customer_email": "TEST_skip@example.com",
            "customer_name": "TEST Skip",
            "agent_id": "iris",
            "level": "demo",
            "days_valid": 7,
            "send_email": False,
        }
        r = http.post(f"{API}/admin/access-links", headers=auth_headers, json=payload, timeout=60)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True
        link = body["link"]
        assert link["agent_id"] == "iris"
        assert link["level"] == "demo"
        assert link["customer_email"] == "test_skip@example.com"  # backend lowercases
        assert link["email_status"] == "skipped"
        assert link["last_sent_at"] is None
        assert link["revoked"] is False
        assert link["url"].startswith("http")
        assert "/mi-agente/" in link["url"]
        assert link["jti"]
        assert "_id" not in link
        _created_link_ids.append(link["id"])
        _created_jtis.append(link["jti"])
        # Save token from URL for validate test
        token = link["url"].rsplit("/", 1)[-1]
        TestAccessLinksFlow._token_skip = token  # type: ignore[attr-defined]
        TestAccessLinksFlow._link_skip_id = link["id"]  # type: ignore[attr-defined]

    def test_create_invalid_agent(self, http, auth_headers):
        r = http.post(f"{API}/admin/access-links", headers=auth_headers, json={
            "customer_email": "TEST_invalid@example.com",
            "agent_id": "doesnotexist",
            "level": "demo",
            "send_email": False,
        }, timeout=60)
        assert r.status_code == 400

    def test_create_with_send_email(self, http, auth_headers):
        # SMTP may fail in preview; that's acceptable -> email_status='failed' but still 200
        # Preview gateway may also 502 if SMTP takes too long; flag as skip
        payload = {
            "customer_email": "TEST_email@example.com",
            "customer_name": "TEST Email",
            "agent_id": "alex",
            "level": "full",
            "send_email": True,
        }
        try:
            r = http.post(f"{API}/admin/access-links", headers=auth_headers, json=payload, timeout=90)
        except requests.exceptions.ReadTimeout:
            pytest.skip("Preview gateway timeout while attempting SMTP send (expected in preview env)")
        if r.status_code in (502, 504):
            pytest.skip(f"Preview gateway returned {r.status_code} during SMTP send (expected in preview env)")
        assert r.status_code == 200, r.text
        link = r.json()["link"]
        assert link["email_status"] in ("sent", "failed")
        _created_link_ids.append(link["id"])
        _created_jtis.append(link["jti"])

    def test_create_unknown_level_normalizes(self, http, auth_headers):
        # After adding a Pydantic field_validator, unknown levels are rejected
        # with a 422 (validation error). Anything else would be a regression.
        r = http.post(f"{API}/admin/access-links", headers=auth_headers, json={
            "customer_email": "TEST_lvl@example.com",
            "agent_id": "umbral",
            "level": "weirdlevel",
            "send_email": False,
        }, timeout=60)
        assert r.status_code == 422, r.text

    def test_list_returns_items(self, http, auth_headers):
        r = http.get(f"{API}/admin/access-links", headers=auth_headers, timeout=60)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        # Our just-created skip link must be in the list
        ids = [it["id"] for it in data["items"]]
        assert getattr(TestAccessLinksFlow, "_link_skip_id", None) in ids
        # Sorted desc by created_at
        if len(data["items"]) >= 2:
            assert data["items"][0]["created_at"] >= data["items"][1]["created_at"]

    def test_validate_token_works(self, http):
        token = getattr(TestAccessLinksFlow, "_token_skip", None)
        assert token, "Token from create test missing"
        r = http.get(f"{API}/access/validate", params={"token": token}, timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["agent_id"] == "iris"
        assert data["level"] == "demo"
        assert data["customer_email"].lower() == "test_skip@example.com"
        assert data["deployment_id"]
        assert "expires_at" in data

    def test_revoke_link(self, http, auth_headers):
        link_id = getattr(TestAccessLinksFlow, "_link_skip_id", None)
        assert link_id
        r = http.post(f"{API}/admin/access-links/{link_id}/revoke", headers=auth_headers, timeout=60)
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        # Idempotent
        r2 = http.post(f"{API}/admin/access-links/{link_id}/revoke", headers=auth_headers, timeout=60)
        assert r2.status_code == 200

    def test_validate_after_revoke(self, http):
        token = getattr(TestAccessLinksFlow, "_token_skip", None)
        assert token
        r = http.get(f"{API}/access/validate", params={"token": token}, timeout=60)
        assert r.status_code == 401
        detail = r.json().get("detail", "").lower()
        assert "revocad" in detail  # "revocado" Spanish

    def test_resend_revoked_returns_400(self, http, auth_headers):
        link_id = getattr(TestAccessLinksFlow, "_link_skip_id", None)
        assert link_id
        r = http.post(f"{API}/admin/access-links/{link_id}/resend", headers=auth_headers, timeout=60)
        assert r.status_code == 400

    def test_resend_unknown_404(self, http, auth_headers):
        r = http.post(f"{API}/admin/access-links/non-existent-id-xyz/resend", headers=auth_headers, timeout=60)
        assert r.status_code == 404

    def test_revoke_unknown_404(self, http, auth_headers):
        r = http.post(f"{API}/admin/access-links/non-existent-id-xyz/revoke", headers=auth_headers, timeout=60)
        assert r.status_code == 404

    def test_delete_unknown_404(self, http, auth_headers):
        r = http.delete(f"{API}/admin/access-links/non-existent-id-xyz", headers=auth_headers, timeout=60)
        assert r.status_code == 404


# ---------- Cleanup ----------

@pytest.fixture(scope="session", autouse=True)
def _cleanup(admin_token):
    yield
    # Delete every TEST_ access link we created
    headers = {"Authorization": f"Bearer {admin_token}"}
    try:
        r = requests.get(f"{API}/admin/access-links", headers=headers, timeout=60)
        if r.status_code == 200:
            for it in r.json().get("items", []):
                if it.get("customer_email", "").lower().startswith("test_"):
                    requests.delete(f"{API}/admin/access-links/{it['id']}", headers=headers, timeout=60)
    except Exception as e:
        print(f"cleanup error: {e}")
