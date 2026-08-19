"""
Input validation utilities for Skill Gap Analyzer.

All validation functions return a (bool, str) tuple:
  (True, "")          → valid
  (False, "message")  → invalid with user-friendly error message
"""

import os
import re
from typing import Tuple

from config.settings import (
    MAX_TEXT_LENGTH,
    MIN_TEXT_LENGTH,
    MAX_NAME_LENGTH,
    MAX_ROLE_LENGTH,
    ALLOWED_EXTENSIONS,
    MAX_CONTENT_LENGTH,
)

ValidationResult = Tuple[bool, str]


def validate_text_input(text: str, field_name: str = "Input") -> ValidationResult:
    """
    Validate that a text field is present, non-empty, and within length limits.

    Args:
        text:       The text value to validate.
        field_name: Human-readable name for error messages.

    Returns:
        (True, "") if valid, (False, error_message) if invalid.
    """
    if not text or not isinstance(text, str):
        return False, f"{field_name} is required."

    stripped = text.strip()
    if len(stripped) < MIN_TEXT_LENGTH:
        return False, (
            f"{field_name} is too short or empty. "
            f"Please provide at least {MIN_TEXT_LENGTH} characters."
        )

    if len(stripped) > MAX_TEXT_LENGTH:
        return False, (
            f"{field_name} is too long. "
            f"Maximum allowed length is {MAX_TEXT_LENGTH:,} characters."
        )

    return True, ""


def validate_name(name: str, field_name: str = "Name") -> ValidationResult:
    """Validate a candidate or role name."""
    if not name or not isinstance(name, str):
        return False, f"{field_name} is required."

    stripped = name.strip()
    if not stripped:
        return False, f"{field_name} cannot be blank."

    if len(stripped) > MAX_NAME_LENGTH:
        return False, (
            f"{field_name} is too long. "
            f"Maximum {MAX_NAME_LENGTH} characters allowed."
        )

    # Only printable characters
    if not re.match(r"^[\w\s\-.,()&']+$", stripped, re.UNICODE):
        return False, (
            f"{field_name} contains invalid characters. "
            "Use letters, numbers, spaces, hyphens, or dots only."
        )

    return True, ""


def validate_file_extension(filename: str) -> ValidationResult:
    """Check that the uploaded file has an allowed extension."""
    if not filename:
        return False, "No filename provided."

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(f".{e}" for e in sorted(ALLOWED_EXTENSIONS))
        return False, (
            f"Unsupported file type '.{ext}'. "
            f"Allowed types: {allowed}."
        )

    return True, ""


def validate_file_size(file_size_bytes: int) -> ValidationResult:
    """Check that uploaded file does not exceed the size limit."""
    if file_size_bytes > MAX_CONTENT_LENGTH:
        limit_mb = MAX_CONTENT_LENGTH / (1024 * 1024)
        return False, (
            f"File is too large. Maximum allowed size is {limit_mb:.0f} MB."
        )
    return True, ""


def validate_analysis_id(value: str) -> ValidationResult:
    """Validate that an analysis ID is a positive integer string."""
    try:
        analysis_id = int(value)
        if analysis_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "Invalid analysis ID. Must be a positive integer."
    return True, ""


def collect_form_errors(**fields) -> dict:
    """
    Validate multiple fields and return a dict of errors.

    Usage::

        errors = collect_form_errors(
            candidate_name=validate_name(name, "Candidate Name"),
            resume_text=validate_text_input(resume, "Resume"),
        )
        if errors:
            ...

    Returns:
        dict mapping field_name → error message for any failed validation.
    """
    errors = {}
    for field_name, (valid, message) in fields.items():
        if not valid:
            errors[field_name] = message
    return errors
