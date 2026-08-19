"""
Data models for Skill Gap Analyzer.

AnalysisResult is a plain Python dataclass that carries all computed
fields for a single skill-gap analysis. Using a dataclass here keeps
the model lightweight and easy to serialize.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional


@dataclass
class SkillEntry:
    """Represents a single skill with its analysis metadata."""
    name: str              # Display name (canonical / normalized)
    category: str          # Skill category from the catalogue
    status: str            # 'matched' | 'partial' | 'missing'
    priority: str = ""     # 'HIGH' | 'MEDIUM' | 'LOW' | '' (for matched)
    priority_reason: str = ""
    importance: str = "required"   # 'required' | 'preferred'
    frequency: int = 1     # How many times it appears in the JD


@dataclass
class RoadmapItem:
    """One step in the recommended learning roadmap."""
    order: int
    skill: str
    category: str
    reason: str


@dataclass
class AnalysisResult:
    """
    Complete result of a skill-gap analysis.

    This is the central data structure that is:
    - produced by ReportGenerator
    - stored as JSON in SQLite
    - passed to Jinja2 templates for rendering
    """

    # ── Input metadata ─────────────────────────────────────────────────────
    candidate_name: str
    target_role: str
    resume_text: str = ""       # kept for display / debugging
    jd_text: str = ""

    # ── Extracted skills ───────────────────────────────────────────────────
    candidate_skills: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)

    # ── Classified skills ──────────────────────────────────────────────────
    matched_skills: List[SkillEntry] = field(default_factory=list)
    partial_skills: List[SkillEntry] = field(default_factory=list)
    missing_skills: List[SkillEntry] = field(default_factory=list)

    # ── Counts ─────────────────────────────────────────────────────────────
    matched_count: int = 0
    partial_count: int = 0
    missing_count: int = 0
    total_required: int = 0

    # ── Score ──────────────────────────────────────────────────────────────
    match_score: float = 0.0     # 0–100 percentage
    score_breakdown: Dict = field(default_factory=dict)

    # ── Priority list ──────────────────────────────────────────────────────
    priority_skills: List[SkillEntry] = field(default_factory=list)

    # ── Roadmap ────────────────────────────────────────────────────────────
    roadmap: List[RoadmapItem] = field(default_factory=list)

    # ── All skills for filter/search in UI ─────────────────────────────────
    all_skills: List[SkillEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to a plain dict suitable for JSON serialization."""
        return asdict(self)

    @property
    def score_label(self) -> str:
        """Human-readable score label."""
        if self.match_score >= 80:
            return "Excellent"
        elif self.match_score >= 60:
            return "Good"
        elif self.match_score >= 40:
            return "Fair"
        else:
            return "Needs Work"

    @property
    def score_color(self) -> str:
        """CSS color class for score display."""
        if self.match_score >= 80:
            return "success"
        elif self.match_score >= 60:
            return "good"
        elif self.match_score >= 40:
            return "warning"
        else:
            return "danger"
