"""
Tests for database layer (AnalysisRepository).

Covers:
  - Save an analysis result
  - Retrieve by ID
  - List (get_all) with search
  - Delete by ID
  - Non-existent ID returns None
  - Missing required fields raise ValueError

Uses a temporary in-memory / temp-file SQLite database so tests
do not pollute the production database.
"""
import os
import sqlite3
import tempfile
import pytest

# Override DATABASE_PATH before importing the module
import config.settings as settings

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def temp_db(tmp_path_factory):
    """Create a temporary SQLite database for testing."""
    db_dir  = tmp_path_factory.mktemp("db")
    db_path = str(db_dir / "test_skillgap.db")

    # Patch settings
    original_path = settings.DATABASE_PATH
    settings.DATABASE_PATH = db_path

    # Reinitialize with patched path
    from database import database as db_module
    db_module.DATABASE_PATH = db_path
    db_module.init_db()

    yield db_module

    # Restore
    settings.DATABASE_PATH = original_path
    db_module.DATABASE_PATH = original_path


@pytest.fixture(scope="module")
def repo(temp_db):
    """Return a fresh AnalysisRepository using the temp DB."""
    from database.database import AnalysisRepository
    return AnalysisRepository()


def sample_result(**overrides) -> dict:
    base = {
        "candidate_name": "Alice Test",
        "target_role":    "Backend Developer",
        "match_score":    72.5,
        "matched_count":  7,
        "partial_count":  1,
        "missing_count":  2,
        "total_required": 10,
        "candidate_skills": ["python", "flask", "sql"],
        "matched_skills": [],
        "missing_skills": [],
        "partial_skills": [],
        "priority_skills": [],
        "roadmap": [],
        "all_skills": [],
        "score_breakdown": {},
    }
    base.update(overrides)
    return base


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_save_returns_positive_id(repo):
    """Saving a valid result should return a positive integer ID."""
    result_id = repo.save(sample_result())
    assert isinstance(result_id, int)
    assert result_id > 0


def test_get_by_id_returns_correct_record(repo):
    """Retrieving by the saved ID should return the correct candidate name."""
    result_id = repo.save(sample_result(candidate_name="BobTest"))
    record = repo.get_by_id(result_id)
    assert record is not None
    assert record["candidate_name"] == "BobTest"


def test_get_by_nonexistent_id_returns_none(repo):
    """Querying a non-existent ID should return None."""
    assert repo.get_by_id(999999) is None


def test_get_all_returns_items(repo):
    """get_all should return a list with at least one item."""
    paginated = repo.get_all()
    assert paginated["total"] >= 1
    assert isinstance(paginated["items"], list)


def test_search_filters_by_candidate_name(repo):
    """Search by candidate name should return only matching records."""
    repo.save(sample_result(candidate_name="SearchableCandidate"))
    paginated = repo.get_all(search="SearchableCandidate")
    names = [item["candidate_name"] for item in paginated["items"]]
    assert "SearchableCandidate" in names


def test_delete_removes_record(repo):
    """Deleting a record should make it unretrievable."""
    result_id = repo.save(sample_result(candidate_name="ToDelete"))
    deleted = repo.delete(result_id)
    assert deleted is True
    assert repo.get_by_id(result_id) is None


def test_delete_nonexistent_returns_false(repo):
    """Attempting to delete a non-existent ID should return False."""
    assert repo.delete(999998) is False


def test_save_missing_field_raises_value_error(repo):
    """Missing required field in result dict should raise ValueError."""
    bad_result = {
        "candidate_name": "X",
        # missing target_role, match_score, etc.
    }
    with pytest.raises(ValueError):
        repo.save(bad_result)


def test_match_score_stored_correctly(repo):
    """Saved match_score should match what is retrieved."""
    result_id = repo.save(sample_result(match_score=88.5))
    record = repo.get_by_id(result_id)
    assert record["match_score"] == 88.5


def test_pagination_works(repo):
    """Paginating with page_size=1 should return exactly 1 item per page."""
    paginated = repo.get_all(page=1, page_size=1)
    assert len(paginated["items"]) == 1
    assert paginated["pages"] >= 1
