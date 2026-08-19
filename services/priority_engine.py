"""
PriorityEngine — assigns HIGH / MEDIUM / LOW priority to missing/partial skills.

Priority scoring factors (each factor adds points):
  +2  Skill is "required" (not preferred)
  +1  Skill appears more than once in the JD (high frequency)
  +1  Skill belongs to a core category (Programming Languages, Backend, Databases)
  -1  Candidate already has a related skill (partial coverage)

Thresholds (from config/settings.py):
  PRIORITY_HIGH_THRESHOLD   >= 3  → HIGH
  PRIORITY_MEDIUM_THRESHOLD >= 1  → MEDIUM
  else                             → LOW
"""
from __future__ import annotations

import logging
from typing import List

from config.settings import PRIORITY_HIGH_THRESHOLD, PRIORITY_MEDIUM_THRESHOLD
from models.analysis import SkillEntry

logger = logging.getLogger(__name__)

_CORE_CATEGORIES = {"Programming Languages", "Backend", "Databases"}

_PRIORITY_LABEL = {
    True: "HIGH",
    False: None,  # placeholder — resolved below
}


class PriorityEngine:
    """
    Assigns priority labels and human-readable reasons to missing/partial skills.

    The priority score is calculated transparently so a developer can explain
    exactly why any skill received a given priority during a viva.
    """

    def assign_priorities(
        self, skills: List[SkillEntry]
    ) -> List[SkillEntry]:
        """
        Compute and attach priority + reason to each SkillEntry in *skills*.

        Args:
            skills: List of SkillEntry objects with status 'missing' or 'partial'.

        Returns:
            The same list, sorted HIGH → MEDIUM → LOW, then alphabetically.
        """
        for entry in skills:
            score, reasons = self._compute_score(entry)
            entry.priority = self._label(score)
            entry.priority_reason = "; ".join(reasons) if reasons else "Low importance"

        return sorted(skills, key=lambda e: (_priority_order(e.priority), e.name))

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _compute_score(entry: SkillEntry) -> "tuple[int, list[str]]":
        """
        Calculate integer priority score and collect reason strings.

        Returns:
            (score: int, reasons: list[str])
        """
        score = 0
        reasons: list[str] = []

        # Factor 1: required vs preferred
        if entry.importance == "required":
            score += 2
            reasons.append("Required skill for the role")

        # Factor 2: frequency in JD
        if entry.frequency > 1:
            score += 1
            reasons.append(f"Mentioned {entry.frequency}x in job description")

        # Factor 3: core category
        if entry.category in _CORE_CATEGORIES:
            score += 1
            reasons.append(f"Core technology category ({entry.category})")

        # Factor 4: partial coverage reduces urgency slightly
        if entry.status == "partial":
            score -= 1
            reasons.append("Partially covered by related skills you already have")

        return score, reasons

    @staticmethod
    def _label(score: int) -> str:
        """Convert numeric priority score to label."""
        if score >= PRIORITY_HIGH_THRESHOLD:
            return "HIGH"
        elif score >= PRIORITY_MEDIUM_THRESHOLD:
            return "MEDIUM"
        else:
            return "LOW"


def _priority_order(label: str) -> int:
    """Sort key: HIGH=0, MEDIUM=1, LOW=2."""
    return {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(label, 3)
