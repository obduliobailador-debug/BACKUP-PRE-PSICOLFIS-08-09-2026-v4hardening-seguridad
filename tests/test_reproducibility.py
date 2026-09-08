"""
Reproducibility / ZIP-audit verification tests.

These tests verify that the files a user would download in a GitHub ZIP
are actually tracked by git and contain no secrets. They exist because a
previous audit (iteration 8 -> user bug report) discovered that .env.example
and yarn.lock files were on the filesystem but NOT tracked by git, so the
downloaded ZIP was missing them.

Run: python3 -m pytest tests/test_reproducibility.py -v
"""
import os
import re
import subprocess
from pathlib import Path

REPO = Path("/app")
TRACKED_FILES = [
    "backend/.env.example",
    "frontend/.env.example",
    "frontend/yarn.lock",
    "RECONSTRUCTION.md",
]
ENV_EXAMPLES = ["backend/.env.example", "frontend/.env.example"]


def run(cmd, cwd=REPO):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=isinstance(cmd, str))


# 1. Files are tracked by git
def test_files_are_git_tracked():
    r = run(["git", "ls-files", "--error-unmatch", *TRACKED_FILES])
    assert r.returncode == 0, f"Untracked files found. stdout={r.stdout} stderr={r.stderr}"


# 2. .env.example + yarn.lock are staged (A ) or already committed (blank)
def test_files_are_staged_or_committed():
    r = run(["git", "status", "--short", *TRACKED_FILES])
    assert r.returncode == 0
    for line in r.stdout.splitlines():
        # If it appears, it must be 'A ' (added/staged) or 'M ' (modified staged).
        # Must NOT be '??' (untracked).
        assert not line.startswith("??"), f"File is untracked: {line}"


# 3. None of the tracked files are gitignored
def test_files_not_gitignored():
    r = run(["git", "check-ignore", *[f for f in TRACKED_FILES if f != "RECONSTRUCTION.md"]])
    # exit code 1 = no paths ignored (what we want). 0 = at least one is ignored (bad).
    assert r.returncode == 1, f"Some files are gitignored: {r.stdout}"


# 4. .env.example files contain no real secrets
FORBIDDEN_LITERALS = ["Clau49006", "Estepo49006"]
SK_LIVE_RE = re.compile(r"sk_live_[a-zA-Z0-9]{20,}")


def test_env_examples_have_no_real_secrets():
    for rel in ENV_EXAMPLES:
        path = REPO / rel
        assert path.exists(), f"{rel} does not exist"
        content = path.read_text()
        for lit in FORBIDDEN_LITERALS:
            assert lit not in content, f"{rel} contains forbidden literal {lit!r}"
        assert not SK_LIVE_RE.search(content), f"{rel} contains a real-looking sk_live_ key"


# 5. yarn.lock is valid v1 lockfile of reasonable size and passes integrity check
def test_yarn_lock_valid():
    lock = REPO / "frontend" / "yarn.lock"
    assert lock.exists(), "yarn.lock missing"
    size = lock.stat().st_size
    assert size >= 400 * 1024, f"yarn.lock too small: {size} bytes"
    header = lock.read_text().splitlines()[:3]
    assert any("yarn lockfile v1" in ln for ln in header), f"Bad header: {header}"

    r = run("yarn check --integrity", cwd=REPO / "frontend")
    combined = (r.stdout + r.stderr).lower()
    # yarn check --integrity prints 'success Folder in sync.' on OK.
    assert r.returncode == 0, f"yarn check failed: {combined}"
    assert "folder in sync" in combined, f"yarn check unexpected output: {combined}"


# 6. Full pytest suite still passes (regression)
# Note: running pytest from inside pytest is fragile; we instead run the two
# suites in subprocesses excluding this file itself to avoid infinite recursion.
def test_regression_suite_passes():
    env = os.environ.copy()
    # Load ADMIN_PASSWORD from backend/.env
    for line in (REPO / "backend" / ".env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip("'").strip('"')
    assert env.get("ADMIN_PASSWORD"), "ADMIN_PASSWORD not found in backend/.env"

    r1 = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "-q", "--tb=short",
         "--ignore=tests/test_reproducibility.py"],
        cwd=REPO, env=env, capture_output=True, text=True,
    )
    r2 = subprocess.run(
        ["python3", "-m", "pytest", "backend/tests/", "-q", "--tb=short"],
        cwd=REPO, env=env, capture_output=True, text=True,
    )
    assert r1.returncode == 0, f"tests/ suite failed:\n{r1.stdout[-2000:]}\n{r1.stderr[-1000:]}"
    assert r2.returncode == 0, f"backend/tests/ suite failed:\n{r2.stdout[-2000:]}\n{r2.stderr[-1000:]}"


# 7. No git-tracked file contains the admin password (old or new)
def test_no_password_in_tracked_files():
    r = run("git ls-files -z | xargs -0 grep -l 'Clau49006\\|Estepo49006' 2>/dev/null || true")
    hits = [ln for ln in r.stdout.splitlines() if ln.strip()]
    # Exclude this test file itself (it must reference the literals to check for them).
    hits = [h for h in hits if not h.endswith("test_reproducibility.py")]
    assert hits == [], f"Password literal found in tracked files: {hits}"
