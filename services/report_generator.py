"""
ReportGenerator — orchestrates all services to produce a complete AnalysisResult.

This is the main entry point called by Flask routes. It:
  1. Normalizes input texts.
  2. Extracts candidate skills and JD skills.
  3. Runs SkillMatcher.
  4. Assigns priorities via PriorityEngine.
  5. Generates a learning roadmap via RoadmapGenerator.
  6. Assembles everything into an AnalysisResult dataclass.
"""

import logging
from typing import List, Optional

from models.analysis import AnalysisResult, SkillEntry
from services.skill_normalizer import SkillNormalizer
from services.skill_extractor import SkillExtractor
from services.skill_matcher import SkillMatcher
from services.priority_engine import PriorityEngine
from services.roadmap_generator import RoadmapGenerator

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Facade that wires all analysis services together.

    Usage::

        rg = ReportGenerator()
        result = rg.generate(
            candidate_name="Alice",
            target_role="Full Stack Developer",
            resume_text="...",
            jd_text="...",
        )
    """

    def __init__(self) -> None:
        self._normalizer = SkillNormalizer()
        self._extractor = SkillExtractor(self._normalizer)
        self._matcher = SkillMatcher(self._normalizer)
        self._priority = PriorityEngine()
        self._roadmap = RoadmapGenerator()

    def generate(
        self,
        candidate_name: str,
        target_role: str,
        resume_text: str,
        jd_text: str,
        manual_required: Optional[List[str]] = None,
        manual_preferred: Optional[List[str]] = None,
    ) -> AnalysisResult:
        """
        Run a complete skill-gap analysis.

        Args:
            candidate_name:    Name of the candidate.
            target_role:       Job role being applied for.
            resume_text:       Full resume/CV text.
            jd_text:           Full job description text.
            manual_required:   Optional user-specified required skills
                               (overrides auto-extraction for required list).
            manual_preferred:  Optional user-specified preferred skills.

        Returns:
            Fully populated AnalysisResult.
        """
        logger.info(
            "Generating analysis for '%s' → '%s'", candidate_name, target_role
        )

        # ── Step 1: Extract candidate skills ──────────────────────────────────
        candidate_skills = self._extractor.extract_skills(resume_text)
        logger.debug("Candidate skills extracted: %s", candidate_skills)

        # ── Step 2: Extract JD skills ─────────────────────────────────────────
        if manual_required is not None:
            required_skills = self._normalizer.normalize_list(manual_required)
            preferred_skills = (
                self._normalizer.normalize_list(manual_preferred)
                if manual_preferred
                else []
            )
        else:
            required_skills, preferred_skills = self._extractor.extract_jd_skills(
                jd_text
            )
        logger.debug("Required: %s | Preferred: %s", required_skills, preferred_skills)

        # ── Step 3: Match skills ───────────────────────────────────────────────
        match_result = self._matcher.match(
            candidate_skills=candidate_skills,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            jd_text=jd_text,
            extractor=self._extractor,
        )

        # ── Step 4: Assign priorities to missing + partial ────────────────────
        skills_needing_priority: List[SkillEntry] = (
            match_result["missing_skills"] + match_result["partial_skills"]
        )
        prioritized = self._priority.assign_priorities(skills_needing_priority)

        # Re-split prioritized list back into missing/partial
        missing_prioritized = [s for s in prioritized if s.status == "missing"]
        partial_prioritized = [s for s in prioritized if s.status == "partial"]

        # ── Step 5: Generate roadmap ───────────────────────────────────────────
        roadmap = self._roadmap.generate(
            missing_skills=missing_prioritized,
            partial_skills=partial_prioritized,
            candidate_skills=candidate_skills,
        )

        # ── Step 6: Build all_skills list (for filter/search UI) ──────────────
        all_skills: List[SkillEntry] = (
            match_result["matched_skills"]
            + partial_prioritized
            + missing_prioritized
        )

        # ── Step 7: Assemble AnalysisResult ───────────────────────────────────
        result = AnalysisResult(
            candidate_name=candidate_name,
            target_role=target_role,
            resume_text=resume_text[:2000],   # truncate for storage efficiency
            jd_text=jd_text[:2000],
            candidate_skills=candidate_skills,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            matched_skills=match_result["matched_skills"],
            partial_skills=partial_prioritized,
            missing_skills=missing_prioritized,
            matched_count=match_result["matched_count"],
            partial_count=match_result["partial_count"],
            missing_count=match_result["missing_count"],
            total_required=match_result["total_required"],
            match_score=match_result["match_score"],
            score_breakdown=match_result["score_breakdown"],
            priority_skills=prioritized,
            roadmap=roadmap,
            all_skills=all_skills,
        )

        logger.info(
            "Analysis complete: score=%.1f%%, matched=%d, partial=%d, missing=%d",
            result.match_score,
            result.matched_count,
            result.partial_count,
            result.missing_count,
        )

        return result
