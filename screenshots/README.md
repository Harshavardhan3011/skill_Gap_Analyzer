# Screenshots — Capture Guide

The automated screenshot tool was unavailable in this environment due to a network limitation.

Please capture the following 12 screenshots manually and save them in this folder.

---

## Recommended filenames

| # | Filename | What to capture |
|---|---|---|
| 1 | `01_home.png` | Home page at `http://127.0.0.1:5000/` |
| 2 | `02_analyze_form.png` | The empty analysis input form at `/analyze` |
| 3 | `03_form_filled.png` | Form filled with sample data (before submit) |
| 4 | `04_result_overview.png` | Result page — top summary cards and score |
| 5 | `05_skill_sections.png` | Matched / Partial / Missing skill badges |
| 6 | `06_priority_table.png` | The Priority Skill Table section |
| 7 | `07_roadmap.png` | The Learning Roadmap section |
| 8 | `08_history.png` | History page at `/history` with at least one record |
| 9 | `09_filter_missing.png` | Result page with "Missing" filter pill active |
| 10 | `10_search_skill.png` | Result page with a skill typed in the search box |
| 11 | `11_validation_error.png` | Empty resume submitted — validation error flash message |
| 12 | `12_error_404.png` | Error page at `/result/999999` |

---

## Step-by-step instructions

### 1. Start the application
```bash
cd c:\Users\harsha\Desktop\skill_gap_analyzer
python app.py
```
Open http://127.0.0.1:5000 in your browser.

### 2. Home page (screenshot 01)
Capture the landing page with the hero section visible.

### 3. Analyze form — empty (screenshot 02)
Click "New Analysis" and capture the blank form.

### 4. Fill the form (screenshot 03)
- Candidate Name: **John Smith**
- Target Role: **Full Stack Developer**
- Resume Text: paste contents of `data/sample_data/sample_resume.txt`
- JD Text: paste contents of `data/sample_data/sample_jd.txt`
- Capture the filled form before clicking Submit.

### 5. Submit and view result (screenshots 04–07)
Click "Run Analysis →". On the result page:
- Capture the top with the score circle and summary cards (04)
- Scroll to skill badges sections — Matched / Partial / Missing (05)
- Scroll to the Priority Table (06)
- Scroll to the Learning Roadmap (07)

### 6. History page (screenshot 08)
Click "View History" in the navbar. Capture the table.

### 7. Filter — Missing skills (screenshot 09)
Return to the result page, click the "Missing" pill filter, capture.

### 8. Search (screenshot 10)
Type "python" in the search box, capture.

### 9. Validation error (screenshot 11)
Go to `/analyze`, leave Resume Text blank, fill everything else,
click Submit. Capture the red error flash message at the top.

### 10. 404 error page (screenshot 12)
Navigate to http://127.0.0.1:5000/result/999999 and capture.

---

## Tips
- Use `Windows + Shift + S` for snipping tool (Windows)
- Or press `F12 → Device toolbar` to see a mobile view too
- Name files exactly as listed above for consistency
