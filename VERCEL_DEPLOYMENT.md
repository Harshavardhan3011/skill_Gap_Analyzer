# Vercel Deployment Guide — Skill Gap Analyzer

## 1. Prerequisites

- A [Vercel account](https://vercel.com) (free tier is sufficient)
- The repository pushed to GitHub: `https://github.com/Harshavardhan3011/skill_Gap_Analyzer`
- Python 3.9+ (for local development)

---

## 2. Repository Setup

Ensure the following files exist at the **project root** before deploying:

| File | Purpose |
|---|---|
| `app.py` | Flask application entry point — exposes `app` at module level |
| `vercel.json` | Vercel build & routing configuration |
| `requirements.txt` | Python dependencies (auto-installed by Vercel) |

---

## 3. Vercel Project Setup

### Option A — Import from GitHub (recommended)

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click **"Import Git Repository"**
3. Select `Harshavardhan3011/skill_Gap_Analyzer`
4. Leave all settings at their defaults (Vercel auto-detects Python from `vercel.json`)
5. Click **Deploy**

### Option B — Vercel CLI

```bash
npm i -g vercel
vercel login
cd path/to/skill_gap_analyzer
vercel
```

Follow the prompts. Select the existing project if prompted.

---

## 4. Build Configuration

`vercel.json` handles everything:

```json
{
  "version": 2,
  "builds": [{ "src": "app.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "app.py" }]
}
```

- **No custom build command needed** — Vercel installs `requirements.txt` automatically.
- **No `Procfile` needed** — `vercel.json` routes all traffic to `app.py`.

---

## 5. Environment Variables

Set these in the Vercel project dashboard → **Settings → Environment Variables**:

| Variable | Description | Required |
|---|---|---|
| `FLASK_SECRET_KEY` | Flask session signing key | **Yes** (for production) |
| `FLASK_DEBUG` | Set to `false` in production | No (defaults to `false`) |

### Setting FLASK_SECRET_KEY

Generate a strong key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output as the value of `FLASK_SECRET_KEY` in Vercel.

**Never commit this value to Git.**

---

## 6. Deployment Steps

### First deployment

1. Push all changes to the `main` branch on GitHub
2. Vercel auto-deploys on every push (if GitHub integration is active)
3. Or trigger manually: Vercel dashboard → **Redeploy**

### Redeploying after code changes

```bash
git add .
git commit -m "Your change description"
git push origin main
```

Vercel detects the push and rebuilds automatically.

---

## 7. Local Verification

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Then open: [http://127.0.0.1:5000](http://127.0.0.1:5000)

### Running tests

```bash
pytest -v
```

All tests must pass before pushing to production.

---

## 8. Common Errors

### `Found app.py but it does not define a top-level "app" Flask instance`

**Cause:** `app` was only assigned inside `if __name__ == "__main__":`.  
**Fix:** `app = create_app()` is now called at module level before the `__main__` block. ✅

### `ModuleNotFoundError` during Vercel build

**Cause:** A dependency is missing from `requirements.txt`.  
**Fix:** Add the missing package to `requirements.txt` and redeploy.

### `500 Internal Server Error` on Vercel

**Cause:** Often a relative path issue (e.g., trying to open a file relative to CWD).  
**Fix:** All paths in this project use `Path(__file__).resolve().parent` — they are absolute and safe.

### `OperationalError: unable to open database file`

**Cause:** Vercel's project filesystem is read-only; SQLite cannot write there.  
**Fix:** `config/settings.py` detects the `VERCEL` environment variable and redirects `DATABASE_PATH` to `/tmp/skillgap.db` automatically. ✅

---

## 9. ⚠️ SQLite / Persistence Limitations on Vercel

> **This is the most important deployment limitation to understand.**

### What works locally

On your local machine, `database/skillgap.db` is a real file that persists across runs. All analysis history is stored and survives restarts.

### What happens on Vercel

Vercel runs Flask as a **serverless function**. Each request may be handled by a fresh container with a clean `/tmp`. This means:

- The SQLite database at `/tmp/skillgap.db` is **ephemeral** — it may be wiped between requests or after a period of inactivity.
- Analysis history **does not reliably persist** across requests on Vercel.
- The analyze → result flow works fine within a single request chain (the redirect to `/result/<id>` happens immediately after saving, so the record exists in that container's `/tmp`).
- The **history page** may appear empty on Vercel, or may lose records between visits.

### What is NOT claimed

This deployment does **not** provide a persistent cloud database. It is a demonstration deployment suitable for showcasing the skill-analysis functionality.

### If persistent history is needed in production

Options (all free-tier available):
- [PlanetScale](https://planetscale.com) — MySQL-compatible, free tier
- [Supabase](https://supabase.com) — PostgreSQL, free tier
- [Railway](https://railway.app) — PostgreSQL, free trial
- [Neon](https://neon.tech) — Serverless PostgreSQL, free tier

These would require replacing the SQLite `database.py` with a PostgreSQL adapter (e.g., `psycopg2` or `SQLAlchemy`).

---

## 10. Deployment Checklist

- [ ] `app.py` exposes `app` at module level (not just inside `__main__`)
- [ ] `vercel.json` exists at project root
- [ ] `requirements.txt` lists all runtime dependencies
- [ ] `FLASK_SECRET_KEY` env var set in Vercel dashboard
- [ ] `FLASK_DEBUG` is `false` (or unset) in Vercel
- [ ] `.env` and `*.db` are in `.gitignore`
- [ ] All tests pass: `pytest -v`
- [ ] App runs locally: `python app.py`
- [ ] Pushed to GitHub `main` branch
