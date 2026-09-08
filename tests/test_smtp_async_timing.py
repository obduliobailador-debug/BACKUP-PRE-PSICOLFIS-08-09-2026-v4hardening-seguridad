"""
Verify SMTP async wrapping (asyncio.to_thread) + 10s timeout on SMTP_SSL.

If SMTP host (psicolfis.net:465) is unreachable from the preview env,
POST /api/contact/budget must return in <15s instead of the old 60-90s.

Only a single hit (spam-conscious per E1 instructions).
"""
import os
import re
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "obdulio@psicolfis.net")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or ""
if not ADMIN_PASSWORD:
    pytest.skip("ADMIN_PASSWORD env var required to run these tests", allow_module_level=True)


def _solve_captcha():
    r = requests.get(f"{BASE_URL}/api/captcha", timeout=10)
    assert r.status_code == 200, r.text
    d = r.json()
    q = d["question"]
    m = re.search(r"(\d+)\s*\+\s*(\d+)", q)
    assert m, f"cannot parse captcha: {q}"
    return d["token"], str(int(m.group(1)) + int(m.group(2)))


class TestBudgetSMTPTiming:
    def test_budget_returns_within_15s_when_smtp_unreachable(self):
        token, ans = _solve_captcha()
        payload = {
            "nombre": "TEST Timing",
            "email": "TEST_timing@example.com",
            "telefono": "600000000",
            "plan": "IRIS - Demo",
            "agente": "IRIS",
            "mensaje": "Test SMTP async timing - not a real request",
            "captcha_token": token,
            "captcha_answer": ans,
        }
        start = time.monotonic()
        r = requests.post(f"{BASE_URL}/api/contact/budget", json=payload, timeout=30)
        elapsed = time.monotonic() - start
        # Acceptable outcomes:
        #  - 200 (SMTP succeeded, email actually sent)
        #  - 502 (SMTP unreachable/timed out - our new behavior)
        assert r.status_code in (200, 502), f"Unexpected status {r.status_code}: {r.text[:200]}"
        # SMTP connect timeout is 10s -> full request must finish well under 15s
        assert elapsed < 15.0, (
            f"Budget endpoint took {elapsed:.1f}s (>=15s). "
            f"SMTP timeout/async-wrap regression. Status: {r.status_code}"
        )
        print(f"budget SMTP call finished in {elapsed:.2f}s, status={r.status_code}")


class TestNoCoroutineBugs:
    """Smoke: /api/webhook/stripe still receives POSTs (signature will fail
    but we just verify no coroutine/awaitable TypeError shows up in response)."""
    def test_stripe_webhook_reachable(self):
        r = requests.post(
            f"{BASE_URL}/api/webhook/stripe",
            data=b"{}",
            headers={"Stripe-Signature": "invalid", "Content-Type": "application/json"},
            timeout=15,
        )
        # 400 (bad signature) is expected; must NOT be 500 with coroutine TypeError.
        assert r.status_code != 500, f"500 from webhook: {r.text[:300]}"
        assert r.status_code in (400, 401, 403), f"Unexpected: {r.status_code} {r.text[:200]}"


class TestAdminAccessLinksSendEmail:
    """/api/admin/access-links (send_email=true) still works — reaches the
    asyncio.to_thread wrapped send_purchase_email path without coroutine bugs."""
    def _login(self):
        r = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        return r.json().get("token")

    def test_access_link_creation_with_send_email(self):
        token = self._login()
        assert token
        start = time.monotonic()
        r = requests.post(
            f"{BASE_URL}/api/admin/access-links",
            json={
                "customer_email": "TEST_asynclink@example.com",
                "customer_name": "TEST AsyncLink",
                "agent_id": "iris",
                "level": "demo",
                "days_valid": 7,
                "send_email": True,
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        elapsed = time.monotonic() - start
        # 200/201 with email_sent boolean expected; 500 would indicate coroutine bug
        assert r.status_code in (200, 201), f"{r.status_code}: {r.text[:300]}"
        assert elapsed < 15.0, f"access-link creation took {elapsed:.1f}s"
        body = r.json()
        # Response shape: {success, link:{email_status:'sent'|'failed'|'skipped', ...}}
        assert "link" in body, f"unexpected body: {body}"
        assert body["link"]["email_status"] in ("sent", "failed", "skipped")
        print(f"access-link created in {elapsed:.2f}s, email_status={body['link']['email_status']}")
