"""
SkillNormalizer — resolves skill name aliases to canonical forms.

All comparisons inside the application are done on normalized skill names
so that "JS", "Javascript", and "JavaScript" are treated identically.
"""

from __future__ import annotations

import json
import re
import logging
from typing import Dict, List, Set

from config.settings import SKILLS_JSON_PATH

logger = logging.getLogger(__name__)


class SkillNormalizer:
    """
    Maps raw skill strings to their canonical normalized forms.

    Normalization steps:
    1. Strip whitespace and lower-case.
    2. Collapse multiple whitespace characters.
    3. Look up in the alias dictionary.
    4. Return the canonical name (already lowercase).

    The alias dictionary is loaded once from data/skills.json.
    """

    def __init__(self) -> None:
        self._aliases: Dict[str, str] = {}
        self._load_aliases()

    def _load_aliases(self) -> None:
        """Load alias map from skills.json."""
        try:
            with open(SKILLS_JSON_PATH, encoding="utf-8") as fh:
                data = json.load(fh)
            self._aliases = data.get("aliases", {})
            logger.debug("Loaded %d skill aliases", len(self._aliases))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Cannot load skills.json: %s", exc)
            self._aliases = {}

    def normalize(self, skill: str) -> str:
        """
        Return the canonical lowercase name for a skill string.

        Args:
            skill: Raw skill name from user input or catalogue.

        Returns:
            Canonical lowercase skill name.
        """
        cleaned = re.sub(r"\s+", " ", skill.strip().lower())
        return self._aliases.get(cleaned, cleaned)

    def normalize_list(self, skills: List[str]) -> List[str]:
        """Normalize a list of skill strings, removing duplicates, preserving order."""
        seen: Set[str] = set()
        result: List[str] = []
        for skill in skills:
            norm = self.normalize(skill)
            if norm and norm not in seen:
                seen.add(norm)
                result.append(norm)
        return result

    def normalize_set(self, skills: List[str]) -> Set[str]:
        """Return a set of normalized skill names."""
        return {self.normalize(s) for s in skills if s.strip()}
