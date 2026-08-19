"""
RoadmapGenerator — builds a rule-based learning roadmap for missing skills.

Ordering logic:
1. HIGH priority skills come before MEDIUM, MEDIUM before LOW.
2. Within the same priority, skills are ordered by their category's
   learning_order from data/skills.json (lower number = learn earlier).
3. Within the same category, foundational skills that are prerequisites
   for other missing skills come first.
4. Each step includes a plain-English reason so the user understands
   why they should learn it in that order.

No external AI or NLP library is used.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, List, Set

from config.settings import SKILLS_JSON_PATH
from models.analysis import RoadmapItem, SkillEntry

logger = logging.getLogger(__name__)

_PREREQS: Dict[str, List[str]] = {
    "node.js": ["javascript"],
    "express.js": ["javascript", "node.js"],
    "react": ["javascript", "html", "css"],
    "angular": ["javascript", "typescript", "html", "css"],
    "vue": ["javascript", "html", "css"],
    "django": ["python"],
    "flask": ["python"],
    "fastapi": ["python"],
    "spring boot": ["java"],
    "tensorflow": ["python", "numpy", "pandas"],
    "pytorch": ["python", "numpy", "pandas"],
    "scikit-learn": ["python", "numpy", "pandas"],
    "kubernetes": ["docker"],
    "ci/cd": ["git", "docker"],
    "graphql": ["rest api"],
    "redux": ["react", "javascript"],
    "typescript": ["javascript"],
}


class RoadmapGenerator:
    """
    Generates a recommended learning sequence for missing/partial skills.

    The roadmap is rule-based and transparent — the reason for each step
    is derived from the priority, category, and prerequisite relationships.
    """

    def __init__(self) -> None:
        self._learning_order: Dict[str, int] = {}
        self._load_learning_order()

    def _load_learning_order(self) -> None:
        """Load category learning order from skills.json."""
        try:
            with open(SKILLS_JSON_PATH, encoding="utf-8") as fh:
                data = json.load(fh)
            self._learning_order = data.get("learning_order", {})
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Cannot load learning_order from skills.json: %s", exc)

    def generate(
        self,
        missing_skills: List[SkillEntry],
        partial_skills: List[SkillEntry],
        candidate_skills: List[str],
    ) -> List[RoadmapItem]:
        """
        Build an ordered learning roadmap.

        Args:
            missing_skills:   Skills the candidate completely lacks.
            partial_skills:   Skills with partial coverage.
            candidate_skills: Already-known skills (to skip in roadmap).

        Returns:
            Ordered list of RoadmapItem objects.
        """
        all_gap_skills = missing_skills + partial_skills
        if not all_gap_skills:
            return []

        # Deduplicate by name
        seen_names: Set[str] = set()
        unique_skills: List[SkillEntry] = []
        for s in all_gap_skills:
            if s.name not in seen_names:
                seen_names.add(s.name)
                unique_skills.append(s)

        sorted_skills = self._topological_sort(unique_skills, set(candidate_skills))
        roadmap: List[RoadmapItem] = []

        for order_idx, entry in enumerate(sorted_skills, start=1):
            reason = self._build_reason(entry, candidate_skills)
            roadmap.append(
                RoadmapItem(
                    order=order_idx,
                    skill=entry.name,
                    category=entry.category,
                    reason=reason,
                )
            )

        return roadmap

    # ── Private helpers ───────────────────────────────────────────────────────

    def _topological_sort(
        self,
        skills: List[SkillEntry],
        known: Set[str],
    ) -> List[SkillEntry]:
        """
        Sort skills so prerequisites appear before dependents,
        then by priority (HIGH first), then by category learning order.
        """
        skill_map = {s.name: s for s in skills}
        result: List[SkillEntry] = []
        visited: Set[str] = set()

        def visit(name: str) -> None:
            if name in visited or name not in skill_map:
                return
            visited.add(name)
            # Visit prerequisites first (if they are also missing)
            for prereq in _PREREQS.get(name, []):
                if prereq not in known:
                    visit(prereq)
            result.append(skill_map[name])

        # Sort input by priority then category learning order before visiting
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_input = sorted(
            skills,
            key=lambda s: (
                priority_order.get(s.priority, 3),
                self._learning_order.get(s.category, 99),
                s.name,
            ),
        )

        for skill in sorted_input:
            visit(skill.name)

        return result

    @staticmethod
    def _build_reason(entry: SkillEntry, candidate_skills: List[str]) -> str:
        """Compose a plain-English reason string."""
        parts: List[str] = []

        if entry.priority == "HIGH":
            parts.append("High priority — required for the target role")
        elif entry.priority == "MEDIUM":
            parts.append("Medium priority — commonly expected skill")
        else:
            parts.append("Good to know — improves overall profile")

        prereqs = _PREREQS.get(entry.name, [])
        satisfied = [p for p in prereqs if p in candidate_skills]
        missing_prereqs = [p for p in prereqs if p not in candidate_skills]

        if satisfied:
            parts.append(
                f"You already know: {', '.join(satisfied)}, "
                "which makes this easier to learn"
            )
        if missing_prereqs:
            parts.append(
                f"Learn after: {', '.join(missing_prereqs)}"
            )

        return ". ".join(parts) + "."
