"""
Pytest configuration and shared fixtures for Skill Gap Analyzer tests.
"""
import os
import sys
import pytest

# ── Ensure the project root is on sys.path ────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(scope="session")
def sample_resume_text() -> str:
    """Realistic sample resume text used across multiple tests."""
    return """
    John Smith - Software Developer

    Skills: Python, JavaScript, HTML, CSS, React, SQL, Git, REST API, pytest

    Experience:
    - Built Flask APIs using Python
    - Developed React frontends
    - Used MySQL and SQLite databases
    - Collaborated with team using GitHub
    """


@pytest.fixture(scope="session")
def sample_jd_text() -> str:
    """Realistic full-stack developer job description."""
    return """
    Full Stack Developer

    Required Skills
    - Python
    - JavaScript
    - React
    - Node.js
    - Express.js
    - MongoDB
    - SQL
    - Git
    - REST API

    Preferred Skills
    - Docker
    - AWS
    - Redis
    - CI/CD
    """
