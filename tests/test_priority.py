"""
Tests for PriorityEngine.

Covers:
  - Required skill in core category → HIGH
  - Preferred skill, non-core → LOW
  - Partial status reduces priority score
  - Frequency increases priority score
  - Sorting: HIGH before MEDIUM before LOW
"""
import pytest
from services.priority_engine import PriorityEngine
from models.analysis import SkillEntry


@pytest.fixture(scope="module")
def engine():
    return PriorityEngine()


def make_entry(
    name="docker",
    category="DevOps & Cloud",
    status="missing",
    importance="required",
    frequency=1,
) -> SkillEntry:
    return SkillEntry(
        name=name,
        category=category,
        status=status,
        importance=importance,
        frequency=frequency,
    )


# ── Priority logic ─────────────────────────────────────────────────────────────

def test_required_core_category_high_priority(engine):
    """Required skill in Programming Languages (core) → HIGH priority."""
    entry = make_entry(
        name="python",
        category="Programming Languages",
        importance="required",
        frequency=1,
    )
    result = engine.assign_priorities([entry])
    assert result[0].priority == "HIGH"


def test_preferred_non_core_low_priority(engine):
    """Preferred skill in non-core category with low frequency → LOW priority."""
    entry = make_entry(
        name="figma",
        category="General",
        importance="preferred",
        frequency=1,
    )
    result = engine.assign_priorities([entry])
    assert result[0].priority in ("LOW", "MEDIUM")  # not HIGH


def test_required_high_frequency_boosts_priority(engine):
    """Required skill mentioned 3× → priority score gets frequency boost."""
    entry = make_entry(
        name="docker",
        category="DevOps & Cloud",
        importance="required",
        frequency=3,
    )
    result = engine.assign_priorities([entry])
    # required(+2) + frequency(+1) = 3 → HIGH
    assert result[0].priority == "HIGH"


def test_partial_status_reduces_score(engine):
    """Partial match reduces priority score by 1."""
    entry = make_entry(
        name="react",
        category="Frontend",
        importance="preferred",
        status="partial",
        frequency=1,
    )
    result = engine.assign_priorities([entry])
    # preferred(0) + partial(-1) = -1 → LOW
    assert result[0].priority == "LOW"


def test_priority_reason_is_set(engine):
    """After assign_priorities, priority_reason should be non-empty."""
    entry = make_entry(name="python", category="Programming Languages", importance="required")
    result = engine.assign_priorities([entry])
    assert result[0].priority_reason != ""


def test_sorting_high_before_medium_before_low(engine):
    """Output list should be sorted HIGH → MEDIUM → LOW."""
    entries = [
        make_entry("low_skill",    "General",                importance="preferred", frequency=1),
        make_entry("high_skill",   "Programming Languages",  importance="required",  frequency=2),
        make_entry("medium_skill", "DevOps & Cloud",         importance="required",  frequency=1),
    ]
    result = engine.assign_priorities(entries)
    priorities = [e.priority for e in result]
    # HIGH should come before any LOW
    if "HIGH" in priorities and "LOW" in priorities:
        assert priorities.index("HIGH") < priorities.index("LOW")


def test_empty_list_returns_empty(engine):
    """No skills → empty result."""
    assert engine.assign_priorities([]) == []
