# TEST_CASES.md — SkillGap Analyzer

**Learn Depth ML Internship — Track 1 — Project #58**

Test command: `pytest tests/ -v`
Total: **62 test cases** — All Passed ✅

---

## Functional Test Cases

| ID | Test Scenario | Input | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| TC-01 | Valid resume + valid JD | Resume with Python/JS/React, JD requiring Python/Node/React/MongoDB | Analysis generated, match_score > 0, result saved to DB | Analysis generated, score = 62.5%, history shows record | ✅ PASS |
| TC-02 | Completely missing skill | Candidate has Python; JD requires Docker | Docker classified as MISSING, score = 0% | Docker → missing, score = 0.0% | ✅ PASS |
| TC-03 | All skills matched | Candidate and JD both have: Python, React, SQL, Git | score = 100%, matched_count = 4, missing = 0 | score = 100.0%, 4 matched | ✅ PASS |
| TC-04 | Duplicate skills in input | Resume says "Python Python Python" | Only 1 Python in extracted skills (deduplicated) | 1 Python in candidate_skills | ✅ PASS |
| TC-05 | Skill alias — JS | Resume says "JS" | Extracted as "javascript" | normalize("JS") = "javascript" | ✅ PASS |
| TC-06 | Skill alias — ReactJS | Text "Built apps using ReactJS." | Extracted as "react" | normalize("ReactJS") = "react" | ✅ PASS |
| TC-07 | Skill alias — NodeJS | Text "NodeJS backend" | Extracted as "node.js" | normalize("NodeJS") = "node.js" | ✅ PASS |
| TC-08 | Empty resume | candidate_name="X", target_role="Y", resume_text="", jd_text=valid JD | Validation error: "Resume is too short or empty" | Flash message shown, form re-rendered | ✅ PASS |
| TC-09 | Empty job description | Valid resume, jd_text="" | Validation error: "Job Description is too short or empty" | Flash message shown | ✅ PASS |
| TC-10 | Empty candidate name | candidate_name="", all other fields valid | Validation error: "Candidate Name is required" | Flash message shown | ✅ PASS |
| TC-11 | Priority calculation — required core skill | Docker, required, core category, freq=3 | Priority = HIGH | Priority = HIGH | ✅ PASS |
| TC-12 | Priority calculation — preferred non-core | Generic tool, preferred, non-core, freq=1 | Priority = LOW or MEDIUM | Priority = LOW | ✅ PASS |
| TC-13 | Partial match via related skills | Candidate has JS+HTML+CSS, JD requires React | React classified as PARTIAL | React → partial, score = 50% | ✅ PASS |
| TC-14 | Score formula verification | 2 required, 1 matched, 1 missing | score = (1×1.0 + 0×0.5) / 2 × 100 = 50% | score = 50.0% | ✅ PASS |
| TC-15 | Preferred skills don't affect score | 1 required (matched), 2 preferred (missing) | score = 100% | score = 100.0% | ✅ PASS |
| TC-16 | DB save and retrieve | Save analysis with match_score=88.5 | Retrieve same score | score=88.5 retrieved | ✅ PASS |
| TC-17 | DB delete | Save then delete analysis | Record not found after delete | get_by_id returns None | ✅ PASS |
| TC-18 | DB search filter | Save analysis with candidate "SearchableCandidate" | Search returns that record | Record returned in results | ✅ PASS |
| TC-19 | Nonexistent DB ID | get_by_id(999999) | Returns None | None returned | ✅ PASS |
| TC-20 | Missing field in result dict | save({candidate_name: "X"}) — missing other fields | ValueError raised | ValueError raised | ✅ PASS |

---

## Route / Integration Test Cases

| ID | Test Scenario | Method | URL | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| TC-21 | Home page loads | GET | / | 200, contains "SkillGap" | 200 ✅ | ✅ PASS |
| TC-22 | Analyze form GET | GET | /analyze | 200, contains "Analysis" | 200 ✅ | ✅ PASS |
| TC-23 | History page loads | GET | /history | 200 | 200 ✅ | ✅ PASS |
| TC-24 | Valid POST → redirect | POST | /analyze (valid data) | 302 redirect to /result/<id> | 302 ✅ | ✅ PASS |
| TC-25 | Result page for valid ID | GET | /result/<id> | 200, "Skill Gap Report" | 200 ✅ | ✅ PASS |
| TC-26 | Result page nonexistent ID | GET | /result/999999 | 404 | 404 ✅ | ✅ PASS |
| TC-27 | JSON API endpoint | GET | /api/analysis/<id> | 200, JSON with match_score | 200, valid JSON ✅ | ✅ PASS |
| TC-28 | Delete analysis | POST | /history/<id>/delete | 302 redirect to /history | 302 ✅ | ✅ PASS |
| TC-29 | Invalid file type upload | POST | /analyze (unsupported file) | Error flash message | Error shown ✅ | ✅ PASS |
| TC-30 | Pagination | get_all(page=1, page_size=1) | 1 item returned, pages >= 1 | 1 item, pages correct ✅ | ✅ PASS |

---

## Normalizer Unit Tests (14 cases)

| ID | Input | Expected Output | Status |
|---|---|---|---|
| TC-N01 | "JS" | "javascript" | ✅ |
| TC-N02 | "Javascript" | "javascript" | ✅ |
| TC-N03 | "ReactJS" | "react" | ✅ |
| TC-N04 | "react.js" | "react" | ✅ |
| TC-N05 | "NodeJS" | "node.js" | ✅ |
| TC-N06 | "Express" | "express.js" | ✅ |
| TC-N07 | "Postgres" | "postgresql" | ✅ |
| TC-N08 | "Mongo" | "mongodb" | ✅ |
| TC-N09 | "ML" | "machine learning" | ✅ |
| TC-N10 | "SomeCustomTech" | "somecustomtech" (pass-through) | ✅ |
| TC-N11 | ["JS","JavaScript","javascript"] | ["javascript"] (1 item) | ✅ |
| TC-N12 | ["Python","JS","python"] | ["python","javascript"] (order preserved) | ✅ |
| TC-N13 | [] | [] | ✅ |
| TC-N14 | normalize_set(["Python","JS","ReactJS"]) | {"python","javascript","react"} | ✅ |

---

## Test Run Summary

```
============================= test session starts =============================
platform win32 -- Python 3.8.10, pytest-8.3.5, pluggy-1.5.0
collected 62 items

tests/test_database.py   ..........   10 passed
tests/test_extractor.py  ..........   10 passed
tests/test_matcher.py    ..........   10 passed
tests/test_normalizer.py ..............  14 passed
tests/test_priority.py   .......    7 passed
tests/test_routes.py     ..........  11 passed

============================= 62 passed in 2.47s ==============================
```

**Result: ALL 62 TESTS PASSED ✅**

---

## How to Run Tests

```bash
cd c:\Users\harsha\Desktop\skill_gap_analyzer
pytest tests/ -v
```
