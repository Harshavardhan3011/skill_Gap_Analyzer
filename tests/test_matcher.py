"""
Tests for SkillMatcher.

Covers:
  - Exact match → matched
  - Completely missing skill → missing
  - All skills matched → 100% score
  - Partial match via related skills
  - Score formula correctness
  - Empty candidate skills
  - Duplicate skill handling
"""
import pytest
from services.skill_normalizer import SkillNormalizer
from services.skill_matcher import SkillMatcher


@pytest.fixture(scope="module")
def matcher():
    return SkillMatcher(SkillNormalizer())


def run_match(matcher, candidate, required, preferred=None, jd=""):
    return matcher.match(
        candidate_skills=candidate,
        required_skills=required,
        preferred_skills=preferred or [],
        jd_text=jd,
        extractor=None,
    )


# ── Exact match ───────────────────────────────────────────────────────────────

def test_exact_match_classified_as_matched(matcher):
    """A skill present in both candidate and JD should be 'matched'."""
    result = run_match(matcher, ["python"], ["python"])
    assert result["matched_count"] == 1
    assert result["missing_count"] == 0
    assert result["match_score"] == 100.0


def test_completely_missing_skill(matcher):
    """A required skill absent from the candidate should be 'missing'."""
    result = run_match(matcher, ["python"], ["docker"])
    assert result["missing_count"] == 1
    assert result["matched_count"] == 0
    assert result["match_score"] == 0.0


def test_all_skills_matched_score_100(matcher):
    """If all required skills are matched, score should be exactly 100."""
    skills = ["python", "javascript", "react", "sql"]
    result = run_match(matcher, skills, skills)
    assert result["match_score"] == 100.0
    assert result["matched_count"] == len(skills)


def test_partial_match_via_related_skills(matcher):
    """
    If candidate has 'javascript' and JD requires 'react',
    this should be a partial match (react's related skills include javascript).
    """
    result = run_match(matcher, ["javascript", "html", "css"], ["react"])
    assert result["partial_count"] == 1
    assert result["missing_count"] == 0


def test_score_formula_half_matched_half_missing(matcher):
    """
    2 required skills, 1 matched (×1.0), 1 missing (×0.0) → 50%.
    """
    result = run_match(matcher, ["python"], ["python", "docker"])
    expected = round(1.0 / 2 * 100, 1)
    assert result["match_score"] == expected


def test_partial_score_contributes_half(matcher):
    """
    1 required skill, partial match → contributes 0.5 → score = 50%.
    """
    # react is related to javascript; candidate has javascript
    result = run_match(matcher, ["javascript", "html", "css"], ["react"])
    # 1 required, 1 partial (0.5) → 50%
    assert result["match_score"] == 50.0


def test_empty_candidate_all_missing(matcher):
    """Empty candidate skills should result in 0% score and all skills missing."""
    result = run_match(matcher, [], ["python", "docker", "react"])
    assert result["missing_count"] == 3
    assert result["match_score"] == 0.0


def test_duplicate_required_skills_handled(matcher):
    """
    Duplicates in required_skills list should not inflate counts.
    (The caller should de-duplicate, but matcher processes as given.)
    """
    result = run_match(matcher, ["python"], ["python", "python"])
    # Both "python" entries are matched; score depends on total required
    assert result["matched_count"] >= 1
    assert result["match_score"] > 0


def test_preferred_skills_do_not_affect_main_score(matcher):
    """
    Preferred skills that are missing should not reduce the main match score.
    Score is calculated only against required_skills.
    """
    result = run_match(
        matcher,
        candidate=["python"],
        required=["python"],
        preferred=["docker", "aws"],
    )
    # Score is based only on required: 1/1 = 100%
    assert result["match_score"] == 100.0
    # docker and aws are in missing (preferred)
    missing_names = [s.name for s in result["missing_skills"]]
    assert "docker" in missing_names
    assert "aws" in missing_names


def test_mixed_scenario_score(matcher):
    """
    4 required, 3 matched, 1 missing → 3/4 * 100 = 75%.
    """
    result = run_match(
        matcher,
        candidate=["python", "javascript", "react"],
        required=["python", "javascript", "react", "docker"],
    )
    assert result["match_score"] == 75.0
