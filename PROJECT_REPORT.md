# PROJECT_REPORT.md — SkillGap Analyzer

**Learn Depth ML Internship — Track 1 — Project #58**
**Student**: (Your Name)
**Date**: August 2026

---

## 1. Problem Understanding

**Original Project #58 requirement:**
> *Compare candidate skills against role requirements and prioritize missing skills.*
> *Expected result: Role-specific skill-gap report.*

The problem addresses a real and practical need: job seekers often do not know exactly which skills they are missing for a target role. Reading a job description and manually comparing it against a resume is:

- Time-consuming
- Inconsistent (different people use different skill names for the same technology)
- Unclear about priority (which missing skill is most important to learn?)

This project automates that entire process and produces a structured, prioritized report.

---

## 2. Requirement Analysis

### Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | Accept candidate resume as text paste or .txt / .pdf file |
| FR-2 | Accept job description as text paste or .txt file |
| FR-3 | Extract technical skills from both inputs |
| FR-4 | Normalize skill name aliases (JS → JavaScript, ReactJS → React) |
| FR-5 | Classify skills as Matched, Partial, or Missing |
| FR-6 | Calculate a transparent weighted match score |
| FR-7 | Assign HIGH / MEDIUM / LOW priority to missing skills |
| FR-8 | Generate a prerequisite-aware learning roadmap |
| FR-9 | Save analyses to a local SQLite database |
| FR-10 | Allow users to view, search, sort, and delete previous analyses |
| FR-11 | Validate all user inputs with meaningful error messages |

### Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | Must work completely offline (no paid APIs) |
| NFR-2 | Must run on Python 3.8+ |
| NFR-3 | Zero external cloud dependencies |
| NFR-4 | Response time < 2 seconds for a typical analysis |
| NFR-5 | Must not crash on invalid user input |
| NFR-6 | Code must follow PEP 8 |
| NFR-7 | Tests must cover all major modules |

---

## 3. Proposed Solution

A Flask web application with a modular service-layer architecture:

```
User (browser)
     ↓  HTTP
Flask Routes (analysis_routes.py)
     ↓
ReportGenerator (orchestrator)
     ↓
┌─────────────┬──────────────┬─────────────┬──────────────┬──────────────┐
│SkillNorm-   │SkillExtractor│SkillMatcher │PriorityEngine│RoadmapGen-   │
│alizer       │              │             │              │erator        │
└─────────────┴──────────────┴─────────────┴──────────────┴──────────────┘
     ↓
AnalysisRepository (SQLite)
     ↓
AnalysisResult (dataclass → JSON → Jinja2 template)
```

Each layer has a single responsibility. No layer knows about Flask internals except the routes.

---

## 4. System Design

### 4.1 Input

| Input | Method | Validation |
|---|---|---|
| Candidate Name | Text field | Max 100 chars, regex check |
| Target Role | Text field | Max 100 chars |
| Resume | Textarea OR .txt/.pdf upload | 10–50,000 chars, max 2 MB |
| Job Description | Textarea OR .txt upload | 10–50,000 chars, max 2 MB |

### 4.2 Skill Extraction

The `SkillExtractor` uses an **n-gram matching** approach:

1. Tokenize text into lowercase word tokens (preserving dots and hyphens)
2. For each position, attempt to match the longest phrase (up to 4 words) against the skill catalogue
3. Resolve the match through the `SkillNormalizer` alias dictionary
4. Record matched skills and skip consumed tokens

The skill catalogue (`data/skills.json`) contains:
- 80+ canonical skill names across 7 categories
- 100+ aliases mapping raw forms to canonical names
- Related-skills map for partial matching
- Category learning-order weights for the roadmap

### 4.3 Skill Normalization

The `SkillNormalizer` applies a pre-loaded alias dictionary:

```python
normalize("ReactJS") → "react"
normalize("JS")       → "javascript"
normalize("Mongo")    → "mongodb"
normalize("ML")       → "machine learning"
```

All comparisons happen on normalized lowercase canonical names.

### 4.4 JD Section Detection

The `SkillExtractor.extract_jd_skills()` method scans for section headers matching patterns like:
- **Required**: `required`, `must have`, `mandatory`, `essential`
- **Preferred**: `preferred`, `nice to have`, `bonus`, `optional`, `plus`

Skills below each header are bucketed accordingly.

### 4.5 Skill Matching

Three classification rules (in order of precedence):

```
1. If skill ∈ candidate_skills  →  MATCHED
2. Elif any related_skills(skill) ∈ candidate_skills  →  PARTIAL
3. Else  →  MISSING
```

### 4.6 Priority Calculation

Four-factor scoring per missing/partial skill:

| Factor | Points |
|---|---|
| Skill is "required" | +2 |
| Frequency in JD > 1 | +1 |
| Core category (Programming Languages / Backend / Databases) | +1 |
| Status is "partial" (already partially covered) | -1 |

Thresholds: ≥3 → HIGH, 1–2 → MEDIUM, ≤0 → LOW

### 4.7 Output

The `AnalysisResult` dataclass is serialized to JSON and:
- Passed to Jinja2 templates for HTML rendering
- Stored in SQLite's `result_json` column for history

### 4.8 Persistence

SQLite `analyses` table with 10 columns:

```sql
CREATE TABLE analyses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_name  TEXT    NOT NULL,
    target_role     TEXT    NOT NULL,
    created_at      TEXT    NOT NULL,
    match_score     REAL    NOT NULL,
    matched_count   INTEGER NOT NULL,
    partial_count   INTEGER NOT NULL,
    missing_count   INTEGER NOT NULL,
    total_required  INTEGER NOT NULL,
    result_json     TEXT    NOT NULL
);
```

---

## 5. Implementation

### Key Modules

| Module | Responsibility |
|---|---|
| `config/settings.py` | All configuration in one place |
| `data/skills.json` | Skill catalogue, aliases, related skills, learning order |
| `database/database.py` | DB init, `AnalysisRepository` CRUD |
| `models/analysis.py` | `AnalysisResult`, `SkillEntry`, `RoadmapItem` dataclasses |
| `services/skill_normalizer.py` | Alias resolution (single-responsibility) |
| `services/skill_extractor.py` | N-gram extraction + JD section detection |
| `services/skill_matcher.py` | Matched/Partial/Missing + scoring |
| `services/priority_engine.py` | 4-factor priority assignment |
| `services/roadmap_generator.py` | Topological-sort learning roadmap |
| `services/report_generator.py` | Orchestrates all 5 services |
| `routes/analysis_routes.py` | Flask routes with validation + error handling |
| `utils/validators.py` | Input validation functions |
| `utils/file_handler.py` | Secure file reading |
| `templates/` | Jinja2 HTML templates |
| `static/` | CSS + Vanilla JS |
| `tests/` | 62 pytest test cases |

---

## 6. Important Technical Decisions

### Why Flask?
- Lightweight and easy to understand
- Standard for Python web internship projects
- Jinja2 templating keeps HTML separate from Python logic
- No frontend framework complexity

### Why SQLite?
- Built into Python (no separate installation)
- Adequate for local single-user persistence
- Simple to inspect with DB Browser for SQLite
- Zero configuration

### Why rule-based skill extraction?
- Works 100% offline
- Fully transparent (can explain every decision)
- Easy to extend the catalogue in `data/skills.json`
- No dependency on paid NLP services

### Why alias normalization?
- Real-world resumes use inconsistent spelling ("JS", "Javascript", "JavaScript")
- Normalization prevents false negatives where identical technologies are missed
- 100+ aliases cover the most common variants

### Why weighted scoring (1.0/0.5/0.0)?
- A partial match is genuinely worth something
- The formula is documented and reproducible
- Different from a random percentage

### Why topological sort in the roadmap?
- Prerequisites should be learned before dependents (e.g., JavaScript before React)
- Makes the learning path practically useful

---

## 7. Data Structures

| Structure | Where Used | Why |
|---|---|---|
| `set` | Candidate skills lookup in SkillMatcher | O(1) membership testing |
| `dict` | Alias map in SkillNormalizer | O(1) alias resolution |
| `dict` | Related-skills map in SkillMatcher | O(1) related lookup |
| `list` | Skill extraction results | Preserve insertion order |
| `list` | Roadmap items | Maintain ordering |
| `dataclass` | AnalysisResult, SkillEntry, RoadmapItem | Type-safe, serializable |
| SQLite row | Analysis persistence | Structured, searchable |
| JSON string | result_json in SQLite | Flexible schema-free detail storage |

---

## 8. Exception Handling

| Scenario | Exception Type | Handling |
|---|---|---|
| Empty resume/JD | (validation) | Flash message, re-render form |
| Unsupported file type | (validation) | Flash message |
| File too large | RequestEntityTooLarge (413) | Global error handler |
| PDF not text-based | OSError / pypdf exception | User-friendly error message |
| DB connection failure | sqlite3.Error | Logged, user sees generic error |
| Analysis ID not found | None check → abort(404) | 404 error page |
| Invalid analysis ID in URL | Flask int converter | 404 automatic |
| Missing fields in result dict | ValueError | Logged, flash warning |
| JSON decode failure | json.JSONDecodeError | Logged, empty catalogue |

All exceptions are specific — no bare `except:` clauses except in pypdf integration (documented with comment).

---

## 9. Testing

### Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.8.10, pytest-8.3.5
collected 62 items

tests/test_database.py   ..........  10 passed
tests/test_extractor.py  ..........  10 passed
tests/test_matcher.py    ..........  10 passed
tests/test_normalizer.py ..............  14 passed
tests/test_priority.py   .......  7 passed
tests/test_routes.py     ..........  11 passed

============================= 62 passed in 2.47s ==============================
```

**All 62 tests passed.**

---

## 10. Challenges Encountered

### Challenge 1: Python 3.8 compatibility
The development environment uses Python 3.8, but modern type hint syntax (`list[str]`, `dict[str, str]`, `set[str]`) requires Python 3.9+.

### Challenge 2: Tokenizer trailing punctuation
`ReactJS.` (with a sentence-ending period) was not matching the alias `reactjs` because the period clung to the token.

### Challenge 3: JD section detection reliability
Automatic detection of "Required" vs "Preferred" sections works when headers are present, but some JDs use different formats.

### Challenge 4: Score denominator
Using total skills (required + preferred) as the denominator would unfairly penalize candidates when a JD has many "nice to have" skills.

---

## 11. Solutions

| Challenge | Solution |
|---|---|
| Python 3.8 types | Added `from __future__ import annotations` and used `typing.List`, `typing.Dict`, `typing.Set` |
| Trailing punctuation | Added a regex `re.sub(r"[.,!?:;]+$", "", token)` step to the tokenizer |
| JD section detection | Falls back to treating all extracted skills as "required" if no section headers are detected |
| Score denominator | Score formula uses only `len(required_skills)` as denominator, ignoring preferred count |

---

## 12. Limitations

- Skill extraction is keyword-based — it cannot infer skills from context
- The alias list covers ~100 common variants; niche aliases may be missed
- PDF support requires text-based PDFs (scanned image PDFs are not supported)
- JD required/preferred split depends on section headers being present
- No semantic understanding (e.g., "software engineering" does not imply "python")
- The skill catalogue covers common tech skills; highly specialized/domain-specific skills may not be recognized
- No authentication or multi-user support

---

## 13. Future Scope

| Feature | Description |
|---|---|
| NLP skill extraction | Use spaCy or NLTK for context-aware extraction |
| Semantic matching | Word embeddings to match semantically similar skills |
| Resume PDF parsing | Structured extraction from LinkedIn PDF exports |
| Role-specific datasets | Different skill catalogues for Data Science, DevOps, Mobile, etc. |
| ML recommendations | Collaborative filtering to suggest what similar candidates learned |
| Export to PDF | Generate a downloadable PDF report |
| Learning resources | Link each missing skill to free courses (Coursera, freeCodeCamp) |
| API mode | REST API for integration with career platforms |
