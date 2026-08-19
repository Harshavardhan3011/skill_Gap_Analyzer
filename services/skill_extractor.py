"""
SkillExtractor — identifies skills mentioned in free text.

Strategy:
1. Load the full skill catalogue from data/skills.json.
2. Build a set of all canonical skill names + their aliases.
3. For each text token/phrase, check against the catalogue (after normalization).
4. Detect JD sections labelled "Required" and "Preferred" to split skills
   into required vs preferred lists. Falls back to treating everything as
   required if no clear section header is found.

This is entirely rule-based — no external AI or NLP libraries required.
"""

import json
import re
import logging
from typing import Dict, List, Tuple, Set

from config.settings import SKILLS_JSON_PATH
from services.skill_normalizer import SkillNormalizer

logger = logging.getLogger(__name__)

# Regex patterns for JD section headers
_REQUIRED_PATTERN = re.compile(
    r"\b(required|must.have|mandatory|essential|primary)\b",
    re.IGNORECASE,
)
_PREFERRED_PATTERN = re.compile(
    r"\b(preferred|nice.to.have|bonus|optional|plus|good.to.have|advantage)\b",
    re.IGNORECASE,
)


class SkillExtractor:
    """
    Extracts skills from plain text using a rule-based catalogue approach.

    Attributes:
        normalizer: SkillNormalizer used for alias resolution.
        catalogue:  Full set of canonical skill names.
        aliases:    Mapping from raw alias to canonical name.
        categories: Mapping from canonical skill to its category.
        max_phrase: Maximum n-gram length to attempt matching (default 4 words).
    """

    def __init__(self, normalizer: SkillNormalizer, max_phrase: int = 4) -> None:
        self.normalizer = normalizer
        self.max_phrase = max_phrase
        self.catalogue: Set[str] = set()
        self.aliases: Dict[str, str] = {}
        self.categories: Dict[str, str] = {}
        self._load_catalogue()

    def _load_catalogue(self) -> None:
        """Load the skill catalogue and build lookup structures."""
        try:
            with open(SKILLS_JSON_PATH, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Cannot load skills.json for extraction: %s", exc)
            return

        self.aliases = data.get("aliases", {})

        for category, meta in data.get("skills", {}).items():
            for skill in meta.get("skills", []):
                norm = self.normalizer.normalize(skill)
                self.catalogue.add(norm)
                self.categories[norm] = category

        # Also add alias targets (already canonical)
        for canonical in self.aliases.values():
            self.catalogue.add(canonical)

        logger.debug(
            "Skill catalogue loaded: %d canonical skills, %d aliases",
            len(self.catalogue),
            len(self.aliases),
        )

    def extract_skills(self, text: str) -> List[str]:
        """
        Extract and normalize all skills found in *text*.

        Args:
            text: Free-form text (resume or JD).

        Returns:
            Deduplicated list of canonical normalized skill names,
            in order of first appearance.
        """
        if not text or not text.strip():
            return []

        tokens = self._tokenize(text)
        return self._match_ngrams(tokens)

    def extract_jd_skills(
        self, jd_text: str
    ) -> Tuple[List[str], List[str]]:
        """
        Extract skills from a job description, splitting into
        required and preferred lists based on section headers.

        Args:
            jd_text: Job description text.

        Returns:
            (required_skills, preferred_skills) — both normalized, deduplicated.
        """
        if not jd_text or not jd_text.strip():
            return [], []

        lines = jd_text.splitlines()
        required: List[str] = []
        preferred: List[str] = []
        seen: Set[str] = set()

        current_section = "required"   # default section

        for line in lines:
            # Detect section header changes
            if _REQUIRED_PATTERN.search(line) and len(line.split()) <= 6:
                current_section = "required"
                continue
            if _PREFERRED_PATTERN.search(line) and len(line.split()) <= 6:
                current_section = "preferred"
                continue

            # Extract skills from this line
            tokens = self._tokenize(line)
            skills = self._match_ngrams(tokens)

            for skill in skills:
                if skill not in seen:
                    seen.add(skill)
                    if current_section == "preferred":
                        preferred.append(skill)
                    else:
                        required.append(skill)

        # Fallback: if nothing labelled as preferred, use full extraction
        if not preferred and not required:
            all_skills = self.extract_skills(jd_text)
            return all_skills, []

        return required, preferred

    def get_category(self, skill: str) -> str:
        """Return the category for a normalized skill name."""
        return self.categories.get(skill, "General")

    def get_skill_frequency(self, skill: str, text: str) -> int:
        """Count how many times a skill (or any alias) appears in text."""
        text_lower = text.lower()
        count = 0

        # Count exact canonical name
        count += len(re.findall(r"\b" + re.escape(skill) + r"\b", text_lower))

        # Count aliases that map to this canonical skill
        for alias, canonical in self.aliases.items():
            if canonical == skill and alias != skill:
                count += len(
                    re.findall(r"\b" + re.escape(alias) + r"\b", text_lower)
                )

        return max(count, 1)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _tokenize(self, text: str) -> List[str]:
        """
        Split text into lowercase word tokens.
        Preserves dots (for 'node.js', 'express.js') and hyphens (for 'scikit-learn').
        """
        # Normalize whitespace but preserve alphanumeric, dots, hyphens, slashes
        cleaned = re.sub(r"[^\w.\-/#+\s]", " ", text.lower())
        tokens = cleaned.split()
        # Strip any trailing dots or punctuation that may cling to tokens
        # (e.g. "ReactJS." → "reactjs")
        return [re.sub(r"[\.\,\!\?\:\;]+$", "", t).strip() for t in tokens if t.strip()]

    def _match_ngrams(self, tokens: List[str]) -> List[str]:
        """
        Attempt to match n-grams (from max_phrase down to 1 word) against
        the catalogue. When a match is found, skip those tokens to avoid
        double-counting.

        Returns deduplicated list of matched canonical skill names.
        """
        found: List[str] = []
        seen: Set[str] = set()
        i = 0

        while i < len(tokens):
            matched = False
            # Try longest phrase first
            for n in range(min(self.max_phrase, len(tokens) - i), 0, -1):
                phrase = " ".join(tokens[i : i + n])
                norm = self.normalizer.normalize(phrase)
                if norm in self.catalogue and norm not in seen:
                    seen.add(norm)
                    found.append(norm)
                    i += n
                    matched = True
                    break
            if not matched:
                i += 1

        return found
