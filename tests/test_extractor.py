"""
Tests for SkillExtractor.

Covers:
  - Extraction from valid resume text
  - Empty text returns empty list
  - Alias extraction (JS, NodeJS, ReactJS in text)
  - JD section splitting (required vs preferred)
  - Multi-word skill extraction (machine learning, rest api)
  - Frequency counting
"""
import pytest
from services.skill_normalizer import SkillNormalizer
from services.skill_extractor import SkillExtractor


@pytest.fixture(scope="module")
def extractor():
    normalizer = SkillNormalizer()
    return SkillExtractor(normalizer)


# ── Basic extraction ──────────────────────────────────────────────────────────

def test_extracts_python(extractor):
    """Python should be detected from resume text."""
    skills = extractor.extract_skills("I know Python and Flask very well.")
    assert "python" in skills


def test_extracts_javascript_from_alias(extractor):
    """JS alias in text should be extracted as 'javascript'."""
    skills = extractor.extract_skills("Frontend work with JS and ReactJS.")
    assert "javascript" in skills


def test_extracts_react_from_reactjs(extractor):
    """ReactJS in text should be extracted as 'react'."""
    skills = extractor.extract_skills("Built apps using ReactJS.")
    assert "react" in skills


def test_extracts_multi_word_skill(extractor):
    """'Machine Learning' should be extracted as 'machine learning'."""
    skills = extractor.extract_skills("Experience with Machine Learning and Deep Learning.")
    assert "machine learning" in skills


def test_empty_text_returns_empty(extractor):
    """Empty text should return an empty list."""
    assert extractor.extract_skills("") == []
    assert extractor.extract_skills("   ") == []


def test_no_duplicates_in_output(extractor):
    """Repeated skill mentions should not produce duplicates."""
    skills = extractor.extract_skills(
        "Python Python Python flask FLASK"
    )
    assert skills.count("python") == 1
    assert skills.count("flask") <= 1


# ── JD section splitting ──────────────────────────────────────────────────────

def test_jd_required_preferred_split(extractor):
    """Required and preferred sections should be correctly split."""
    jd = """
    Required Skills
    Python
    Node.js
    SQL

    Preferred Skills
    Docker
    AWS
    """
    required, preferred = extractor.extract_jd_skills(jd)
    assert "python" in required
    assert "node.js" in required
    assert "docker" in preferred
    assert "aws" in preferred


def test_jd_empty_returns_empty(extractor):
    """Empty JD text should return empty lists."""
    req, pref = extractor.extract_jd_skills("")
    assert req == []
    assert pref == []


# ── Frequency ─────────────────────────────────────────────────────────────────

def test_frequency_counting(extractor):
    """A skill mentioned multiple times should have frequency > 1."""
    text = "Python developer. Python experience required. Strong Python skills."
    freq = extractor.get_skill_frequency("python", text)
    assert freq >= 3


def test_category_lookup(extractor):
    """python should be in 'Programming Languages'."""
    cat = extractor.get_category("python")
    assert cat == "Programming Languages"
