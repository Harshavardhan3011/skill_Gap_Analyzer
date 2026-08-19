"""
Integration tests for Flask routes.

Covers:
  - Home page loads (200)
  - Analyze page GET (200)
  - Analyze POST with valid data → redirect to result
  - Analyze POST with empty resume → validation error flash
  - Analyze POST with empty JD → validation error flash
  - Analyze POST with empty candidate name → validation error
  - Result page for valid ID (200)
  - Result page for nonexistent ID (404)
  - History page (200)
  - Delete analysis

Uses Flask test client with an isolated temp database.
"""
import os
import sys
import tempfile
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """Create a test Flask client with an isolated temp database."""
    import config.settings as settings

    db_dir  = tmp_path_factory.mktemp("route_db")
    db_path = str(db_dir / "routes_test.db")

    # Patch before import of app
    settings.DATABASE_PATH = db_path

    from database import database as db_module
    db_module.DATABASE_PATH = db_path

    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.test_client() as c:
        yield c


RESUME = (
    "Skills: Python, JavaScript, HTML, CSS, React, SQL, Git, REST API"
)
JD = (
    "Required Skills: Python, Node.js, React, MongoDB, SQL, Git, REST API\n"
    "Preferred Skills: Docker, AWS"
)


# ── Home & static pages ───────────────────────────────────────────────────────

def test_home_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"SkillGap" in resp.data


def test_analyze_page_get(client):
    resp = client.get("/analyze")
    assert resp.status_code == 200
    assert b"Analysis" in resp.data


def test_history_page_loads(client):
    resp = client.get("/history")
    assert resp.status_code == 200


# ── POST validation ───────────────────────────────────────────────────────────

def test_analyze_post_empty_resume_shows_error(client):
    resp = client.post("/analyze", data={
        "candidate_name": "Test User",
        "target_role":    "Developer",
        "resume_text":    "",          # Empty
        "jd_text":        JD,
    })
    assert resp.status_code == 200   # Re-renders form
    assert b"short or empty" in resp.data or b"required" in resp.data.lower()


def test_analyze_post_empty_jd_shows_error(client):
    resp = client.post("/analyze", data={
        "candidate_name": "Test User",
        "target_role":    "Developer",
        "resume_text":    RESUME,
        "jd_text":        "",          # Empty
    })
    assert resp.status_code == 200
    assert b"short or empty" in resp.data or b"required" in resp.data.lower()


def test_analyze_post_empty_name_shows_error(client):
    resp = client.post("/analyze", data={
        "candidate_name": "",          # Empty
        "target_role":    "Developer",
        "resume_text":    RESUME,
        "jd_text":        JD,
    })
    assert resp.status_code == 200
    assert b"required" in resp.data.lower() or b"blank" in resp.data.lower()


def test_analyze_post_valid_redirects_to_result(client):
    """A valid POST should redirect (302) to the result page."""
    resp = client.post("/analyze", data={
        "candidate_name": "RouteTestUser",
        "target_role":    "Full Stack Developer",
        "resume_text":    RESUME,
        "jd_text":        JD,
    }, follow_redirects=False)
    # Should redirect to /result/<id>
    assert resp.status_code == 302
    assert "/result/" in resp.headers.get("Location", "")


def test_result_page_loads_after_analysis(client):
    """After a valid analysis, the result page should return 200."""
    resp = client.post("/analyze", data={
        "candidate_name": "ResultTestUser",
        "target_role":    "Developer",
        "resume_text":    RESUME,
        "jd_text":        JD,
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Skill Gap Report" in resp.data


def test_result_page_nonexistent_id_returns_404(client):
    resp = client.get("/result/999999")
    assert resp.status_code == 404


def test_api_json_endpoint(client):
    """The JSON API endpoint should return JSON for a valid analysis."""
    # First create one
    r = client.post("/analyze", data={
        "candidate_name": "APITest",
        "target_role":    "Developer",
        "resume_text":    RESUME,
        "jd_text":        JD,
    }, follow_redirects=False)
    location = r.headers.get("Location", "")
    analysis_id = location.rstrip("/").split("/")[-1]

    resp = client.get(f"/api/analysis/{analysis_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data is not None
    assert "match_score" in data


def test_delete_analysis(client):
    """Delete endpoint should redirect to history."""
    # Create an analysis to delete
    r = client.post("/analyze", data={
        "candidate_name": "DeleteTestUser",
        "target_role":    "Developer",
        "resume_text":    RESUME,
        "jd_text":        JD,
    }, follow_redirects=False)
    location = r.headers.get("Location", "")
    analysis_id = location.rstrip("/").split("/")[-1]

    resp = client.post(f"/history/{analysis_id}/delete", follow_redirects=False)
    assert resp.status_code == 302
    assert "history" in resp.headers.get("Location", "")
