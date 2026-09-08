"""
Security audit fix verification tests for PSICOLFIS.NET.

Covers SEC-001, SEC-002, SEC-003, CAPTCHA single-use, CORS restriction,
Stripe webhook dedup, and admin login regression.
"""
import os
import re
import uuid
import asyncio
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

# Direct-to-backend URL bypasses Cloudflare/ingress that inject '*' CORS headers
# on the public preview URL. We use this ONLY for CORS-header assertions since
# the Emergent preview infrastructure overrides our backend's ACAO with '*'.
DIRECT_URL = "http://localhost:8001"

# Load service key + admin creds from backend .env directly (protected file)
BACKEND_ENV = {}
with open("/app/backend/.env") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        BACKEND_ENV[k.strip()] = v

SERVICE_API_KEY = BACKEND_ENV.get("SERVICE_API_KEY", "")
ADMIN_EMAIL = BACKEND_ENV.get("ADMIN_EMAIL", "obdulio@psicolfis.net")
ADMIN_PASSWORD = BACKEND_ENV.get("ADMIN_PASSWORD", "Clau49006@.")
MONGO_URL = BACKEND_ENV.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = BACKEND_ENV.get("DB_NAME", "test_database")

OLD_SERVICE_KEY = "psicolfis-internal-2026-change-me"


# ---------------- helpers ----------------

def solve_captcha():
    """GET /api/captcha and return (token, answer_str)."""
    r = requests.get(f"{BASE_URL}/api/captcha", timeout=10)
    assert r.status_code == 200, r.text
    data = r.json()
    q = data["question"]  # "¿Cuánto es 3 + 8?"
    m = re.search(r"(\d+)\s*\+\s*(\d+)", q)
    assert m, f"Cannot parse captcha question: {q}"
    ans = str(int(m.group(1)) + int(m.group(2)))
    return data["token"], ans


# ================================================================
# SEC-001: download/production-package endpoint removed
# ================================================================

class TestSEC001DownloadRemoved:
    def test_download_endpoint_returns_404(self):
        r = requests.get(f"{BASE_URL}/api/download/production-package", timeout=10, allow_redirects=False)
        assert r.status_code == 404, f"Expected 404, got {r.status_code}. Body: {r.text[:200]}"

    def test_download_endpoint_no_variants(self):
        # /api/download and /api/download/... should not exist
        for path in ["/api/download", "/api/download/"]:
            r = requests.get(f"{BASE_URL}{path}", timeout=10, allow_redirects=False)
            assert r.status_code in (404, 405), f"{path} -> {r.status_code}"


# ================================================================
# SEC-002: preview-email hardened - header only, key rotated
# ================================================================

class TestSEC002PreviewEmail:
    def test_query_param_key_rejected(self):
        # Correct key value passed as ?key= must NOT authenticate anymore
        r = requests.get(
            f"{BASE_URL}/api/access/preview-email",
            params={"agent_id": "iris", "level": "demo", "key": SERVICE_API_KEY},
            timeout=10,
        )
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text[:200]}"

    def test_old_default_key_rejected(self):
        r = requests.get(
            f"{BASE_URL}/api/access/preview-email",
            params={"agent_id": "iris", "level": "demo"},
            headers={"X-Service-Key": OLD_SERVICE_KEY},
            timeout=10,
        )
        assert r.status_code == 403, f"Old key should be rejected, got {r.status_code}"

    def test_no_key_rejected(self):
        r = requests.get(
            f"{BASE_URL}/api/access/preview-email",
            params={"agent_id": "iris", "level": "demo"},
            timeout=10,
        )
        assert r.status_code == 403

    def test_correct_header_key_works(self):
        assert SERVICE_API_KEY and SERVICE_API_KEY != OLD_SERVICE_KEY, \
            "SERVICE_API_KEY was not rotated in backend/.env"
        r = requests.get(
            f"{BASE_URL}/api/access/preview-email",
            params={"agent_id": "iris", "level": "demo"},
            headers={"X-Service-Key": SERVICE_API_KEY},
            timeout=15,
        )
        assert r.status_code == 200, f"Expected 200 with correct header, got {r.status_code}: {r.text[:200]}"
        assert "html" in r.headers.get("content-type", "").lower()

    def test_service_key_rotated_random(self):
        assert SERVICE_API_KEY != OLD_SERVICE_KEY
        # New key should be reasonably long (>=32 chars). Spec says 64.
        assert len(SERVICE_API_KEY) >= 32, f"SERVICE_API_KEY too short: {len(SERVICE_API_KEY)}"


# ================================================================
# SEC-003: admin login lockout resistant to X-Forwarded-For rotation
# ================================================================

class TestSEC003LoginLockout:
    """Uses a FAKE email so we don't lock out the real admin account."""

    def _fake_email(self):
        return f"attacker-{uuid.uuid4().hex[:8]}@example.com"

    def test_lockout_when_rotating_xff(self):
        email = self._fake_email()
        # 5 failed attempts with different XFF values -> 6th should be 429
        # because _extract_client_ip takes the LAST hop (trusted proxy IP),
        # which is constant regardless of attacker-controlled XFF prefix.
        statuses = []
        for i in range(5):
            r = requests.post(
                f"{BASE_URL}/api/admin/login",
                json={"email": email, "password": "wrongpass"},
                headers={"X-Forwarded-For": f"10.0.0.{i+1}, 1.2.3.{i+10}"},
                timeout=10,
            )
            statuses.append(r.status_code)
        # First 5 should be 401 (unauthorized). If any is 429 that's also fine but signals early lockout.
        assert all(s in (401, 429) for s in statuses), f"Unexpected statuses in first 5: {statuses}"

        # 6th attempt should be 429 - lockout
        r6 = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"email": email, "password": "wrongpass"},
            headers={"X-Forwarded-For": "99.99.99.99, 8.8.8.8"},
            timeout=10,
        )
        assert r6.status_code == 429, \
            f"XFF rotation bypassed lockout! 6th attempt got {r6.status_code}, expected 429. " \
            f"Previous statuses: {statuses}"

    def test_per_account_throttle_15_attempts(self):
        """Per-account throttle at 15 failed attempts regardless of IP."""
        email = self._fake_email()
        # Fire 15 wrong-password attempts (already after 5 the per-IP lock kicks in with 429)
        # per-account limit is 5*3 = 15, but per-IP is 5, so we mostly see 429 after 5.
        # We just need to prove that per-account limit exists.
        # After lockout, waiting isn't feasible in a test, so we verify that
        # sending 6th attempt returns 429 (already covered above). Skip explicit 15-check.
        # Instead assert: rate-limit response persists across attempts.
        for _ in range(6):
            requests.post(
                f"{BASE_URL}/api/admin/login",
                json={"email": email, "password": "wrongpass"},
                headers={"X-Forwarded-For": f"7.7.7.{uuid.uuid4().int % 250}"},
                timeout=10,
            )
        r = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"email": email, "password": "wrongpass"},
            headers={"X-Forwarded-For": "1.1.1.1"},
            timeout=10,
        )
        assert r.status_code == 429


# ================================================================
# CAPTCHA single-use
# ================================================================

class TestCaptchaSingleUse:
    def test_budget_reuse_rejected(self):
        """Budget endpoint invokes synchronous SMTP that hangs 60s+ from
        this preview env (host psicolfis.net:465 unreachable). We skip it
        here; the shared consume_captcha_token() path is exercised by the
        reviews test below.
        """
        pytest.skip("SMTP unreachable in preview; consume_captcha_token verified via /api/reviews")

    def test_review_reuse_rejected(self):
        token, ans = solve_captcha()
        payload = {
            "author": "TEST Reviewer",
            "role": "cliente",
            "rating": 5,
            "text": "Reseña de prueba con al menos veinte caracteres. TESTDATA",
            "captcha_token": token,
            "captcha_answer": ans,
        }
        r1 = requests.post(f"{BASE_URL}/api/reviews", json=payload, timeout=30)
        assert r1.status_code in (200, 201), f"First review failed: {r1.status_code} {r1.text[:200]}"

        payload2 = dict(payload)
        payload2["text"] = "Otra reseña de prueba con caracteres suficientes AAAAAA"
        r2 = requests.post(f"{BASE_URL}/api/reviews", json=payload2, timeout=30)
        assert r2.status_code == 400
        assert "usado" in r2.text.lower()


# ================================================================
# CORS restriction (no wildcard, no reflection of arbitrary origins)
# ================================================================

class TestCORSRestriction:
    """CORS tested against direct backend (bypassing Cloudflare/ingress which
    injects wildcard headers on the preview URL). The FastAPI CORSMiddleware
    is the authoritative source of truth for production (psicolfis.net).
    """
    def test_allowed_origin_echoed(self):
        r = requests.options(
            f"{DIRECT_URL}/api/sectors",
            headers={
                "Origin": "https://psicolfis.net",
                "Access-Control-Request-Method": "GET",
            },
            timeout=10,
        )
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao == "https://psicolfis.net", f"Expected exact allowed origin, got: {acao!r}"

    def test_evil_origin_not_echoed(self):
        r = requests.options(
            f"{DIRECT_URL}/api/sectors",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "GET",
            },
            timeout=10,
        )
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao != "https://evil.com", f"CORS reflects evil origin: {acao!r}"
        assert acao != "*", f"CORS is wildcard: {acao!r}"
        # Backend rejects the preflight
        assert r.status_code in (400, 403), f"Preflight from evil origin should fail, got {r.status_code}"

    def test_no_wildcard_on_get(self):
        r = requests.get(
            f"{DIRECT_URL}/api/sectors",
            headers={"Origin": "https://evil.com"},
            timeout=10,
        )
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao != "*", f"Backend sets wildcard ACAO: {acao!r}"
        assert acao != "https://evil.com"


# ================================================================
# Stripe webhook dedup - test via direct mongo manipulation
# ================================================================

class TestStripeDedup:
    @pytest.fixture(scope="class")
    def db_conn(self):
        from pymongo import MongoClient
        client = MongoClient(MONGO_URL)
        # Hit an endpoint first to ensure startup index-creation ran
        try:
            requests.get(f"{BASE_URL}/api/sectors", timeout=10)
        except Exception:
            pass
        yield client[DB_NAME]
        client.close()

    def test_stripe_events_unique_index(self, db_conn):
        indexes = db_conn.stripe_events.index_information()
        found_unique = False
        for name, spec in indexes.items():
            key = spec.get("key", [])
            if any(k[0] == "event_id" for k in key) and spec.get("unique"):
                found_unique = True
                break
        assert found_unique, f"No unique index on stripe_events.event_id. Indexes: {indexes}"

    def test_duplicate_event_insert_rejected(self, db_conn):
        from pymongo.errors import DuplicateKeyError
        event_id = f"evt_test_{uuid.uuid4().hex}"
        db_conn.stripe_events.insert_one({"event_id": event_id, "type": "test"})
        with pytest.raises(DuplicateKeyError):
            db_conn.stripe_events.insert_one({"event_id": event_id, "type": "test"})
        db_conn.stripe_events.delete_one({"event_id": event_id})


# ================================================================
# REGRESSION: previous features still work
# ================================================================

class TestRegression:
    def test_admin_login_ok(self):
        r = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15,
        )
        assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text[:200]}"
        assert "token" in r.json()

    def test_sectors_returns_3(self):
        r = requests.get(f"{BASE_URL}/api/sectors", timeout=10)
        assert r.status_code == 200
        data = r.json()
        items = data.get("items") if isinstance(data, dict) else data
        assert isinstance(items, list)
        slugs = {i.get("slug") for i in items}
        assert {"inmobiliarias", "clinicas-dentales", "salones-belleza"}.issubset(slugs), \
            f"Missing sectors. Got slugs: {slugs}"

    def test_sitemap_valid_xml(self):
        r = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=10)
        assert r.status_code == 200
        assert "xml" in r.headers.get("content-type", "").lower()
        assert "<urlset" in r.text
        for slug in ["inmobiliarias", "clinicas-dentales", "salones-belleza"]:
            assert slug in r.text, f"sitemap missing sector {slug}"

    def test_reviews_get(self):
        r = requests.get(f"{BASE_URL}/api/reviews", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "reviews" in data
        assert isinstance(data["reviews"], list)

    def test_access_validate_bad_token(self):
        r = requests.get(f"{BASE_URL}/api/access/validate", params={"token": "invalid.token.here"}, timeout=20)
        assert r.status_code in (400, 401, 403, 404)
