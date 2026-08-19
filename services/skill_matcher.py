"""
SkillMatcher — compares candidate skills against job requirements.

Classification:
  matched  — candidate has the required skill exactly (after normalization).
  partial  — candidate lacks the skill but has a clearly related skill.
  missing  — skill is absent and no related skill found.

Score formula (documented in README):
  score = (matched * 1.0 + partial * 0.5) / total_required * 100
"""

import json
import logging
from typing import Dict, List, Set, Tuple

from config.settings import SKILLS_JSON_PATH, SCORE_MATCHED, SCORE_PARTIAL
from models.analysis import SkillEntry
from services.skill_normalizer import SkillNormalizer

logger = logging.getLogger(__name__)


class SkillMatcher:
    """
    Compares normalized candidate skills against required/preferred skills
    and classifies each into matched / partial / missing.

    Uses a related-skills map from data/skills.json to detect partial matches.
    A partial match means the candidate has a skill in the same technology family
    even if not the exact required skill.
    """

    def __init__(self, normalizer: SkillNormalizer) -> None:
        self.normalizer = normalizer
        self._related: Dict[str, List[str]] = {}
        self._load_related()

    def _load_related(self) -> None:
        """Load the related-skills map from data/skills.json."""
        try:
            with open(SKILLS_JSON_PATH, encoding="utf-8") as fh:
                data = json.load(fh)
            self._related = data.get("related_skills", {})
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Cannot load related skills: %s", exc)
            self._related = {}

    def match(
        self,
        candidate_skills: List[str],
        required_skills: List[str],
        preferred_skills: List[str],
        jd_text: str,
        extractor=None,
    ) -> Dict:
        """
        Perform the full matching comparison.

        Args:
            candidate_skills: Normalized candidate skills.
            required_skills:  Normalized required JD skills.
            preferred_skills: Normalized preferred JD skills.
            jd_text:          Raw JD text for frequency analysis.
            extractor:        Optional SkillExtractor for frequency counts.

        Returns:
            dict with keys:
              matched_skills, partial_skills, missing_skills,
              matched_count, partial_count, missing_count,
              total_required, match_score, score_breakdown
        """
        candidate_set: Set[str] = set(candidate_skills)

        matched: List[SkillEntry] = []
        partial: List[SkillEntry] = []
        missing: List[SkillEntry] = []

        # Process required skills
        for skill in required_skills:
            entry = self._classify_skill(
                skill, candidate_set, "required", jd_text, extractor
            )
            _bucket(entry, matched, partial, missing)

        # Process preferred skills
        for skill in preferred_skills:
            if skill in [s.name for s in matched + partial + missing]:
                continue  # already classified as required
            entry = self._classify_skill(
                skill, candidate_set, "preferred", jd_text, extractor
            )
            _bucket(entry, matched, partial, missing)

        total_required = len(required_skills)

        # Score calculation (only against required skills)
        req_matched = sum(1 for s in matched if s.importance == "required")
        req_partial = sum(1 for s in partial if s.importance == "required")

        if total_required > 0:
            raw_score = (
                req_matched * SCORE_MATCHED + req_partial * SCORE_PARTIAL
            ) / total_required * 100
            match_score = round(min(raw_score, 100.0), 1)
        else:
            match_score = 0.0

        score_breakdown = {
            "matched_weighted": req_matched * SCORE_MATCHED,
            "partial_weighted": req_partial * SCORE_PARTIAL,
            "total_required": total_required,
            "formula": (
                f"({req_matched}×1.0 + {req_partial}×0.5) "
                f"/ {total_required} × 100"
            ),
        }

        return {
            "matched_skills": matched,
            "partial_skills": partial,
            "missing_skills": missing,
            "matched_count": len(matched),
            "partial_count": len(partial),
            "missing_count": len(missing),
            "total_required": total_required,
            "match_score": match_score,
            "score_breakdown": score_breakdown,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _classify_skill(
        self,
        skill: str,
        candidate_set: Set[str],
        importance: str,
        jd_text: str,
        extractor,
    ) -> SkillEntry:
        """Classify a single skill as matched, partial, or missing."""
        freq = extractor.get_skill_frequency(skill, jd_text) if extractor else 1
        category = extractor.get_category(skill) if extractor else "General"

        if skill in candidate_set:
            return SkillEntry(
                name=skill,
                category=category,
                status="matched",
                importance=importance,
                frequency=freq,
            )

        # Check for partial match via related skills
        related = self._related.get(skill, [])
        if any(r in candidate_set for r in related):
            matching_related = [r for r in related if r in candidate_set]
            return SkillEntry(
                name=skill,
                category=category,
                status="partial",
                importance=importance,
                frequency=freq,
                priority_reason=(
                    f"Related skill(s) found: "
                    f"{', '.join(matching_related)}"
                ),
            )

        return SkillEntry(
            name=skill,
            category=category,
            status="missing",
            importance=importance,
            frequency=freq,
        )

    def is_related(self, skill_a: str, skill_b: str) -> bool:
        """Check if two skills are related (bidirectional)."""
        return (
            skill_b in self._related.get(skill_a, [])
            or skill_a in self._related.get(skill_b, [])
        )


# ── Module-level helper ───────────────────────────────────────────────────────

def _bucket(
    entry: SkillEntry,
    matched: List[SkillEntry],
    partial: List[SkillEntry],
    missing: List[SkillEntry],
) -> None:
    """Append SkillEntry to the correct bucket."""
    if entry.status == "matched":
        matched.append(entry)
    elif entry.status == "partial":
        partial.append(entry)
    else:
        missing.append(entry)
