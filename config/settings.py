"""
Application configuration settings for Skill Gap Analyzer.
All configurable parameters live here so other modules import from one place.
"""

import os

# ── Base paths ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_DIR = os.path.join(BASE_DIR, "database")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

# ── Flask ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "skillgap-dev-secret-2024-local-only")
DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_PATH = os.path.join(DATABASE_DIR, "skillgap.db")

# ── File uploads ──────────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {"txt", "pdf"}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB limit

# ── Skill data ────────────────────────────────────────────────────────────────
SKILLS_JSON_PATH = os.path.join(DATA_DIR, "skills.json")

# ── Scoring weights ───────────────────────────────────────────────────────────
SCORE_MATCHED = 1.0
SCORE_PARTIAL = 0.5
SCORE_MISSING = 0.0

# ── Priority thresholds ───────────────────────────────────────────────────────
PRIORITY_HIGH_THRESHOLD = 3
PRIORITY_MEDIUM_THRESHOLD = 1

# ── Pagination ────────────────────────────────────────────────────────────────
HISTORY_PAGE_SIZE = 10

# ── Input limits ─────────────────────────────────────────────────────────────
MAX_TEXT_LENGTH = 50_000   # characters
MIN_TEXT_LENGTH = 10       # characters — below this is considered empty
MAX_NAME_LENGTH = 100
MAX_ROLE_LENGTH = 100
