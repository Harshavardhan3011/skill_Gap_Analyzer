# SkillGap Analyzer

> **Learn Depth ML Internship — Track 1 — Project #58**

A web-based application that compares candidate skills against job description requirements, identifies skill gaps, prioritizes missing skills, and generates a detailed role-specific skill-gap report.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [Objective](#objective)
4. [Features](#features)
5. [Technologies Used](#technologies-used)
6. [System Requirements](#system-requirements)
7. [Installation](#installation)
8. [Setup](#setup)
9. [How to Run](#how-to-run)
10. [How the Skill Matching Algorithm Works](#how-the-skill-matching-algorithm-works)
11. [Match Score Formula](#match-score-formula)
12. [Priority Algorithm](#priority-algorithm)
13. [Project Structure](#project-structure)
14. [Database Design](#database-design)
15. [Testing](#testing)
16. [Sample Usage](#sample-usage)
17. [Screenshots](#screenshots)
18. [Limitations](#limitations)
19. [Future Improvements](#future-improvements)
20. [Learning Outcomes](#learning-outcomes)

---

## 1. Project Overview

SkillGap Analyzer is a **Python + Flask web application** that compares candidate skills (extracted from a resume or skills list) against role requirements (extracted from a job description). It produces a detailed, prioritized skill-gap report with:

- Matched / Partial / Missing skill classification
- A transparent weighted match score
- HIGH / MEDIUM / LOW priority ranking for missing skills
- A prerequisite-aware learning roadmap
- SQLite-persisted analysis history

The application works **100% offline** after installation. No paid APIs, cloud services, or internet connection is required.

---

## 2. Problem Statement

Job seekers often apply for roles without knowing which specific skills they lack. Manually comparing a resume against a JD is time-consuming and inconsistent. Common problems:

- Skill aliases create confusion ("JS" vs "JavaScript")
- No clear prioritization of what to learn first
- No persistent record of analyses across sessions

---

## 3. Objective

> **Project #58**: Compare candidate skills against role requirements and prioritize missing skills.
> **Expected Result**: Role-specific skill-gap report.

This application provides:
- Automated extraction of skills from free text
- Normalization of 100+ skill aliases
- Three-tier classification: Matched, Partial, Missing
- Quantitative match score with documented formula
- Prioritized list of missing skills with explanations
- Rule-based learning roadmap
- Persistent analysis history

---

## 4. Features

| Feature | Description |
|---|---|
| Paste or upload resume | Textarea or .txt / .pdf file upload |
| Paste or upload JD | Textarea or .txt file upload |
| Skill extraction | Rule-based, 80+ skills, 100+ aliases |
| Alias normalization | JS→JavaScript, ReactJS→React, Mongo→MongoDB |
| Required/Preferred split | Auto-detected from JD section headers |
| Matched/Partial/Missing | Three-tier skill classification |
| Weighted match score | Transparent formula, 0–100% |
| Priority ranking | HIGH / MEDIUM / LOW with reasons |
| Learning roadmap | Prerequisite-aware ordering |
| Analysis history | SQLite persistence |
| Search/filter/sort | On history and result pages |
| Delete analysis | From history page |
| Responsive UI | Mobile-friendly layout |
| Validation | Input length, file type, file size |
| Error handling | Specific exceptions, user-friendly messages |

---

## 5. Technologies Used

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Web Framework | Flask 3.x |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Templates | Jinja2 |
| Database | SQLite (built into Python) |
| PDF support | pypdf (optional) |
| Testing | pytest |
| File handling | Werkzeug |

---

## 6. System Requirements

- Python 3.11 or higher
- pip (Python package manager)
- A modern web browser (Chrome, Firefox, Edge)
- No internet connection required after installation

---

## 7. Installation

```bash
# 1. Navigate to the project directory
cd skill-gap-analyzer

# 2. (Recommended) Create a virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 8. Setup

No additional setup is required. The SQLite database is created automatically on first run at `database/skillgap.db`.

The skill catalogue is loaded from `data/skills.json` at startup.

---

## 9. How to Run

```bash
python app.py
```

Then open your browser and go to:

```
http://127.0.0.1:5000
```

The application will be ready to use.

---

## 10. How the Skill Matching Algorithm Works

### Step 1 — Skill Extraction

The `SkillExtractor` uses an n-gram approach:
1. Tokenize the text into words.
2. Try to match the longest phrase (up to 4 words) against the skill catalogue.
3. If a match is found, record it and skip those words.
4. Repeat for all tokens.

The skill catalogue (`data/skills.json`) contains 80+ skills across 7 categories.

### Step 2 — Skill Normalization

The `SkillNormalizer` applies a dictionary of 100+ aliases:

```
JS         → javascript
ReactJS    → react
NodeJS     → node.js
Postgres   → postgresql
ML         → machine learning
```

All comparisons are done on normalized lowercase skill names.

### Step 3 — JD Section Detection

The `SkillExtractor.extract_jd_skills()` method scans JD text for lines containing section headers like "Required", "Must Have", "Preferred", "Nice to Have". Skills below each header are placed in the corresponding bucket.

### Step 4 — Matching

The `SkillMatcher` classifies each required skill as:

| Status | Condition |
|---|---|
| **Matched** | Skill found exactly in candidate's normalized skill set |
| **Partial** | Skill not found, but a related skill (same technology family) is present |
| **Missing** | Skill not found, no related skills found either |

Related skills are defined in `data/skills.json` under `related_skills`. Example: if React is required but missing, and the candidate has JavaScript + HTML + CSS, React is classified as **Partial**.

### Step 5 — Priority Assignment

The `PriorityEngine` scores each missing/partial skill on four factors and assigns HIGH / MEDIUM / LOW.

### Step 6 — Learning Roadmap

The `RoadmapGenerator` orders missing/partial skills by:
1. Priority (HIGH first)
2. Category learning order (foundational first)
3. Prerequisite relationships (learn JavaScript before React)

---

## 11. Match Score Formula

```
score = (matched × 1.0 + partial × 0.5) / total_required × 100
```

Only **required** skills (not preferred) are counted in the denominator.

**Example:**
```
Required skills = 10
Matched = 6   → 6 × 1.0 = 6.0
Partial = 2   → 2 × 0.5 = 1.0
Missing = 2   → 2 × 0.0 = 0.0

Score = (6.0 + 1.0) / 10 × 100 = 70.0%
```

Score labels:
- 80–100% → Excellent
- 60–79%  → Good
- 40–59%  → Fair
- 0–39%   → Needs Work

---

## 12. Priority Algorithm

Each missing or partial skill receives a priority score:

| Factor | Points |
|---|---|
| Skill is marked "required" (not preferred) | +2 |
| Skill appears more than once in the JD | +1 |
| Skill belongs to a core category (Programming Languages, Backend, Databases) | +1 |
| Skill has partial coverage (candidate has related skill) | -1 |

**Thresholds:**
- Score ≥ 3 → **HIGH**
- Score 1–2 → **MEDIUM**
- Score ≤ 0 → **LOW**

The priority label and a plain-English reason are shown in the Priority Table on the result page.

---

## 13. Project Structure

```
skill-gap-analyzer/
│
├── app.py                 # Flask app factory, entry point
├── requirements.txt       # Python dependencies
├── README.md
├── PROJECT_REPORT.md
├── TEST_CASES.md
├── .gitignore
│
├── config/
│   └── settings.py        # All configurable parameters
│
├── data/
│   ├── skills.json        # Skill catalogue + aliases + related skills
│   └── sample_data/
│       ├── sample_resume.txt
│       └── sample_jd.txt
│
├── database/
│   ├── database.py        # AnalysisRepository (CRUD)
│   └── skillgap.db        # Created at runtime
│
├── models/
│   └── analysis.py        # AnalysisResult, SkillEntry, RoadmapItem dataclasses
│
├── services/
│   ├── skill_normalizer.py  # Alias resolution
│   ├── skill_extractor.py   # N-gram extraction + JD section detection
│   ├── skill_matcher.py     # Matched/Partial/Missing + score
│   ├── priority_engine.py   # HIGH/MEDIUM/LOW priority assignment
│   ├── roadmap_generator.py # Prerequisite-aware learning roadmap
│   └── report_generator.py  # Orchestrates all services
│
├── routes/
│   ├── main_routes.py     # Home page
│   └── analysis_routes.py # Analyze, result, history, delete, API
│
├── utils/
│   ├── validators.py      # Input validation functions
│   └── file_handler.py    # Secure .txt and .pdf file reading
│
├── templates/
│   ├── base.html          # Navbar, flash messages, footer
│   ├── index.html         # Landing page
│   ├── analyze.html       # Input form (paste + upload tabs)
│   ├── result.html        # Result dashboard
│   ├── history.html       # Analysis history
│   └── error.html         # Error page
│
├── static/
│   ├── css/style.css      # Full stylesheet
│   └── js/app.js          # Tabs, drag-drop, filter, sort
│
├── tests/
│   ├── conftest.py
│   ├── test_normalizer.py
│   ├── test_extractor.py
│   ├── test_matcher.py
│   ├── test_priority.py
│   ├── test_database.py
│   └── test_routes.py
│
└── screenshots/
    └── README.md
```

---

## 14. Database Design

Single table: `analyses`

| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| candidate_name | TEXT | Candidate name (max 100 chars) |
| target_role | TEXT | Job role applied for |
| created_at | TEXT | Timestamp (YYYY-MM-DD HH:MM:SS) |
| match_score | REAL | Match percentage (0–100) |
| matched_count | INTEGER | Number of matched skills |
| partial_count | INTEGER | Number of partial skills |
| missing_count | INTEGER | Number of missing skills |
| total_required | INTEGER | Total required skills |
| result_json | TEXT | Full analysis as JSON string |

Indexed on: `created_at DESC`, `candidate_name`.

All queries use parameterized SQL (no string formatting) to prevent SQL injection.

---

## 15. Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module
pytest tests/test_matcher.py -v
```

**Test modules:**
- `test_normalizer.py` — 14 alias/normalization tests
- `test_extractor.py` — 10 extraction tests
- `test_matcher.py` — 10 matching and scoring tests
- `test_priority.py` — 7 priority assignment tests
- `test_database.py` — 10 CRUD and edge-case tests
- `test_routes.py` — 10 Flask route integration tests

Total: **61 test cases**

---

## 16. Sample Usage

1. Run `python app.py`
2. Go to `http://127.0.0.1:5000`
3. Click **New Analysis**
4. Enter candidate name: `John Smith`
5. Enter target role: `Full Stack Developer`
6. Paste the content of `data/sample_data/sample_resume.txt`
7. Paste the content of `data/sample_data/sample_jd.txt`
8. Click **Run Analysis**
9. View the result dashboard
10. Go to **History** to see the saved analysis

---

## 17. Screenshots

See `screenshots/README.md` for capture instructions.

---

## 18. Limitations

- Skill extraction is keyword/catalogue-based — it cannot understand context
- Two different spellings not covered by the alias list may be missed
- PDF extraction only works for text-based PDFs (not scanned images)
- The required/preferred split depends on JD section headers being present
- No semantic understanding — "software engineer" does not imply "python"
- The skill catalogue covers ~80 common tech skills; niche skills may not be recognized

---

## 19. Future Improvements

- Add NLP-based skill extraction (spaCy, NLTK) for better coverage
- Semantic skill matching using word embeddings
- Resume parsing from structured formats (LinkedIn PDF export)
- More job-role-specific skill datasets
- ML-based recommendation of learning resources
- Email report delivery
- Multi-user authentication
- Import/export analysis as PDF report

---

## 20. Learning Outcomes

By building this project, I learned and applied:

- Python OOP (classes, dataclasses, encapsulation)
- Flask web framework (blueprints, routes, Jinja2, request handling)
- SQLite database with parameterized queries
- File I/O (text files, PDF extraction)
- Sets, dictionaries, and lists for skill matching algorithms
- Algorithm design (n-gram matching, topological sort, weighted scoring)
- Input validation and exception handling best practices
- pytest unit and integration testing
- Modular code organization
- Professional project documentation
