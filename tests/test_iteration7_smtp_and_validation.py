"""
Iteration 7 verification:
1. SMTP-bounded: /api/contact/budget <15s (target <13s) when SMTP unreachable
2. SMTP-bounded: /api/admin/access-links (send_email=true) <15s
3. Level validation: 'invalid' -> 422; 'demo' / 'full' OK; 'DEMO' -> normalized to 'demo'
4. Regression: /api/sectors returns 3 items; admin login OK
5. Regression: /api/reviews accepts a review with fresh captcha
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

ADMIN_EMAIL = "obdulio@psicolfis.net"
ADMIN_PASSWORD = "Clau49006@."


def _solve_captcha():
    r = requests.get(f"{BASE_URL}/api/captcha", timeout=10)
    assert r.status_code == 200, r.text
    d = r.json()
    q = d["question"]
    m = re.search(r"(\d+)\s*\+\s*(\d+)", q)
    assert m, f"cannot parse captcha: {q}"
    return d["token"], str(int(m.group(1)) + int(m.group(2)))


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/admin/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    tok = r.json().get("token")
    assert tok
    return tok


# ---- 1. SMTP bounded on /api/contact/budget --------------------------------

def test_budget_bounded_under_15s_when_smtp_unreachable():
    token, ans = _solve_captcha()
    payload = {
        "nombre": "TEST Iter7",
        "email": "TEST_iter7_budget@example.com",
        "telefono": "600000000",
        "plan": "IRIS - Demo",
        "agente": "IRIS",
        "mensaje": "Iter7 SMTP bounded timing test",
        "captcha_token": token,
        "captcha_answer": ans,
    }
    start = time.monotonic()
    r = requests.post(f"{BASE_URL}/api/contact/budget", json=payload, timeout=25)
    elapsed = time.monotonic() - start
    print(f"[budget] elapsed={elapsed:.2f}s status={r.status_code}")
    assert r.status_code in (200, 502), f"unexpected {r.status_code}: {r.text[:200]}"
    assert elapsed < 15.0, f"Budget took {elapsed:.2f}s (>=15s)"


# ---- 2. SMTP bounded on /api/admin/access-links ----------------------------

def test_access_links_send_email_bounded_under_15s(admin_token):
    start = time.monotonic()
    r = requests.post(
        f"{BASE_URL}/api/admin/access-links",
        json={
            "customer_email": "TEST_iter7_link@example.com",
            "customer_name": "TEST Iter7 Link",
            "agent_id": "iris",
            "level": "demo",
            "days_valid": 7,
            "send_email": True,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=25,
    )
    elapsed = time.monotonic() - start
    print(f"[access-links send_email] elapsed={elapsed:.2f}s status={r.status_code}")
    assert r.status_code in (200, 201), f"{r.status_code}: {r.text[:300]}"
    assert elapsed < 15.0, f"access-links took {elapsed:.2f}s (>=15s)"
    body = r.json()
    # response wraps link under "link" key; email_status reflects delivery outcome
    assert body.get("success") is True
    link = body.get("link", {})
    assert "email_status" in link, f"missing email_status: {body}"


# ---- 3. AdminAccessLinkRequest.level validation ----------------------------

def test_level_invalid_returns_422(admin_token):
    r = requests.post(
        f"{BASE_URL}/api/admin/access-links",
        json={
            "customer_email": "TEST_iter7_invalidlvl@example.com",
            "customer_name": "TEST",
            "agent_id": "iris",
            "level": "invalid",
            "days_valid": 7,
            "send_email": False,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=15,
    )
    assert r.status_code == 422, f"expected 422 for level=invalid, got {r.status_code}: {r.text[:300]}"


def test_level_demo_ok(admin_token):
    r = requests.post(
        f"{BASE_URL}/api/admin/access-links",
        json={
            "customer_email": "TEST_iter7_demo@example.com",
            "customer_name": "TEST",
            "agent_id": "iris",
            "level": "demo",
            "days_valid": 7,
            "send_email": False,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=15,
    )
    assert r.status_code in (200, 201), f"{r.status_code}: {r.text[:200]}"
    assert r.json().get("link", {}).get("level") == "demo"


def test_level_full_ok(admin_token):
    r = requests.post(
        f"{BASE_URL}/api/admin/access-links",
        json={
            "customer_email": "TEST_iter7_full@example.com",
            "customer_name": "TEST",
            "agent_id": "iris",
            "level": "full",
            "days_valid": 7,
            "send_email": False,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=15,
    )
    assert r.status_code in (200, 201), f"{r.status_code}: {r.text[:200]}"
    assert r.json().get("link", {}).get("level") == "full"


def test_level_uppercase_normalizes_to_demo(admin_token):
    r = requests.post(
        f"{BASE_URL}/api/admin/access-links",
        json={
            "customer_email": "TEST_iter7_upperdemo@example.com",
            "customer_name": "TEST",
            "agent_id": "iris",
            "level": "DEMO",
            "days_valid": 7,
            "send_email": False,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=15,
    )
    assert r.status_code in (200, 201), f"{r.status_code}: {r.text[:200]}"
    assert r.json().get("link", {}).get("level") == "demo", f"expected demo normalization, got {r.json()}"


# ---- 4. Regression: sectors + admin login ----------------------------------

def test_sectors_returns_three_items():
    r = requests.get(f"{BASE_URL}/api/sectors", timeout=10)
    assert r.status_code == 200
    data = r.json()
    # accept either list or dict shape
    items = data if isinstance(data, list) else data.get("sectors") or data.get("items") or []
    assert len(items) == 3, f"expected 3 sectors, got {len(items)}: {data}"


def test_admin_login_ok():
    r = requests.post(
        f"{BASE_URL}/api/admin/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200
    assert "token" in r.json()


# ---- 5. Regression: /api/reviews with fresh captcha ------------------------

def test_reviews_creates_with_fresh_captcha():
    token, ans = _solve_captcha()
    payload = {
        "author": "TEST Iter7 Reviewer",
        "rating": 5,
        "text": "Regression test iter7 - fresh captcha review submission.",
        "role": "Cliente",
        "captcha_token": token,
        "captcha_answer": ans,
    }
    r = requests.post(f"{BASE_URL}/api/reviews", json=payload, timeout=15)
    # 200/201 success; 202 pending moderation also acceptable
    assert r.status_code in (200, 201, 202), f"{r.status_code}: {r.text[:300]}"
