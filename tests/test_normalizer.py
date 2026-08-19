"""
Tests for SkillNormalizer.

Covers:
  - Basic normalization (lowercase, whitespace)
  - Alias resolution (JS→javascript, ReactJS→react, etc.)
  - Deduplication in normalize_list
  - Unknown skills pass through unchanged
"""
import pytest
from services.skill_normalizer import SkillNormalizer


@pytest.fixture(scope="module")
def normalizer():
    return SkillNormalizer()


# ── Alias resolution ──────────────────────────────────────────────────────────

def test_js_to_javascript(normalizer):
    """JS alias should resolve to 'javascript'."""
    assert normalizer.normalize("JS") == "javascript"


def test_javascript_case_insensitive(normalizer):
    """'Javascript' (mixed case) should normalize to 'javascript'."""
    assert normalizer.normalize("Javascript") == "javascript"


def test_reactjs_to_react(normalizer):
    """ReactJS should normalize to 'react'."""
    assert normalizer.normalize("ReactJS") == "react"


def test_react_dot_js(normalizer):
    """React.js should normalize to 'react'."""
    assert normalizer.normalize("react.js") == "react"


def test_nodejs_to_node_js(normalizer):
    """NodeJS should normalize to 'node.js'."""
    assert normalizer.normalize("NodeJS") == "node.js"


def test_express_to_express_js(normalizer):
    """'Express' alias should resolve to 'express.js'."""
    assert normalizer.normalize("Express") == "express.js"


def test_postgres_to_postgresql(normalizer):
    """'Postgres' alias should resolve to 'postgresql'."""
    assert normalizer.normalize("Postgres") == "postgresql"


def test_mongo_to_mongodb(normalizer):
    """'Mongo' alias should resolve to 'mongodb'."""
    assert normalizer.normalize("Mongo") == "mongodb"


def test_ml_to_machine_learning(normalizer):
    """'ML' alias should resolve to 'machine learning'."""
    assert normalizer.normalize("ML") == "machine learning"


def test_unknown_skill_passes_through(normalizer):
    """An unrecognized skill should be lowercased but otherwise unchanged."""
    result = normalizer.normalize("SomeCustomTech")
    assert result == "somecustomtech"


# ── normalize_list ─────────────────────────────────────────────────────────────

def test_normalize_list_deduplication(normalizer):
    """Duplicate aliases that resolve to the same canonical name should be deduplicated."""
    raw = ["JS", "JavaScript", "javascript"]
    result = normalizer.normalize_list(raw)
    assert result.count("javascript") == 1


def test_normalize_list_preserves_order(normalizer):
    """First occurrence should be preserved, later duplicates dropped."""
    raw = ["Python", "JS", "python"]
    result = normalizer.normalize_list(raw)
    assert result[0] == "python"
    assert result[1] == "javascript"
    assert len(result) == 2


def test_normalize_list_empty(normalizer):
    assert normalizer.normalize_list([]) == []


def test_normalize_set_returns_set(normalizer):
    raw = ["Python", "JS", "ReactJS"]
    result = normalizer.normalize_set(raw)
    assert isinstance(result, set)
    assert "python" in result
    assert "javascript" in result
    assert "react" in result
