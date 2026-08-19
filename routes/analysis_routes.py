"""
Analysis routes — form submission, result display, history, delete.

All routes handle:
  - Input validation (via utils/validators.py)
  - Exception handling (specific exceptions, no bare except)
  - User-friendly error flash messages
  - Redirect after POST (PRG pattern) to prevent duplicate submissions
"""

import logging
import sqlite3

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    abort,
)

from config.settings import HISTORY_PAGE_SIZE
from database.database import AnalysisRepository
from services.report_generator import ReportGenerator
from utils.validators import (
    validate_name,
    validate_text_input,
    validate_analysis_id,
    collect_form_errors,
)
from utils.file_handler import FileHandler

logger = logging.getLogger(__name__)

analysis_bp = Blueprint("analysis", __name__)

# Module-level singletons (created once per process)
_repo = AnalysisRepository()
_generator = ReportGenerator()
_file_handler = FileHandler()


# ── Analyze ───────────────────────────────────────────────────────────────────

@analysis_bp.route("/analyze", methods=["GET", "POST"])
def analyze():
    """
    GET:  Display the analysis input form.
    POST: Process the form, run analysis, save to DB, redirect to result.
    """
    if request.method == "GET":
        return render_template("analyze.html")

    # ── Collect form data ──────────────────────────────────────────────────
    candidate_name = request.form.get("candidate_name", "").strip()
    target_role = request.form.get("target_role", "").strip()

    # Resume: text area OR file upload
    resume_text = request.form.get("resume_text", "").strip()
    resume_file = request.files.get("resume_file")
    if resume_file and resume_file.filename:
        ok, result = _file_handler.read_uploaded_file(resume_file)
        if not ok:
            flash(result, "error")
            return render_template("analyze.html", form_data=request.form)
        resume_text = result

    # JD: text area OR file upload
    jd_text = request.form.get("jd_text", "").strip()
    jd_file = request.files.get("jd_file")
    if jd_file and jd_file.filename:
        ok, result = _file_handler.read_uploaded_file(jd_file)
        if not ok:
            flash(result, "error")
            return render_template("analyze.html", form_data=request.form)
        jd_text = result

    # ── Validate ───────────────────────────────────────────────────────────
    errors = collect_form_errors(
        candidate_name=validate_name(candidate_name, "Candidate Name"),
        target_role=validate_name(target_role, "Target Role"),
        resume_text=validate_text_input(resume_text, "Resume / Candidate Info"),
        jd_text=validate_text_input(jd_text, "Job Description"),
    )

    if errors:
        for msg in errors.values():
            flash(msg, "error")
        return render_template("analyze.html", form_data=request.form)

    # ── Run analysis ───────────────────────────────────────────────────────
    try:
        result = _generator.generate(
            candidate_name=candidate_name,
            target_role=target_role,
            resume_text=resume_text,
            jd_text=jd_text,
        )
    except Exception as exc:
        logger.error("Analysis generation failed: %s", exc, exc_info=True)
        flash("An error occurred during analysis. Please try again.", "error")
        return render_template("analyze.html", form_data=request.form)

    # ── Save to database ───────────────────────────────────────────────────
    try:
        analysis_id = _repo.save(result.to_dict())
    except (sqlite3.Error, ValueError) as exc:
        logger.error("Failed to save analysis: %s", exc, exc_info=True)
        flash("Analysis complete, but could not save to database.", "warning")
        # Still show the result by passing it directly
        return render_template("result.html", result=result.to_dict(), analysis_id=None)

    return redirect(url_for("analysis.result", analysis_id=analysis_id))


# ── Result ────────────────────────────────────────────────────────────────────

@analysis_bp.route("/result/<int:analysis_id>")
def result(analysis_id: int):
    """Display the full skill-gap analysis report."""
    try:
        data = _repo.get_by_id(analysis_id)
    except sqlite3.Error as exc:
        logger.error("DB error fetching analysis %s: %s", analysis_id, exc)
        flash("Database error. Please try again.", "error")
        return redirect(url_for("main.index"))

    if data is None:
        abort(404)

    return render_template("result.html", result=data, analysis_id=analysis_id)


# ── History ───────────────────────────────────────────────────────────────────

@analysis_bp.route("/history")
def history():
    """Display paginated analysis history with search/filter/sort."""
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort_by", "created_at")
    order = request.args.get("order", "desc")
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1

    try:
        paginated = _repo.get_all(
            search=search,
            sort_by=sort_by,
            order=order,
            page=page,
            page_size=HISTORY_PAGE_SIZE,
        )
    except sqlite3.Error as exc:
        logger.error("DB error listing analyses: %s", exc)
        flash("Could not load analysis history.", "error")
        paginated = {"items": [], "total": 0, "page": 1, "pages": 1}

    return render_template(
        "history.html",
        analyses=paginated["items"],
        total=paginated["total"],
        page=paginated["page"],
        pages=paginated["pages"],
        search=search,
        sort_by=sort_by,
        order=order,
    )


# ── Delete ────────────────────────────────────────────────────────────────────

@analysis_bp.route("/history/<int:analysis_id>/delete", methods=["POST"])
def delete_analysis(analysis_id: int):
    """Delete an analysis record (POST for CSRF safety)."""
    try:
        deleted = _repo.delete(analysis_id)
    except sqlite3.Error as exc:
        logger.error("DB error deleting analysis %s: %s", analysis_id, exc)
        flash("Failed to delete the analysis. Please try again.", "error")
        return redirect(url_for("analysis.history"))

    if deleted:
        flash("Analysis deleted successfully.", "success")
    else:
        flash("Analysis not found.", "warning")

    return redirect(url_for("analysis.history"))


# ── JSON API (for advanced JS use) ───────────────────────────────────────────

@analysis_bp.route("/api/analysis/<int:analysis_id>")
def api_get_analysis(analysis_id: int):
    """Return analysis as JSON (useful for frontend JS)."""
    try:
        data = _repo.get_by_id(analysis_id)
    except sqlite3.Error as exc:
        logger.error("API DB error: %s", exc)
        return jsonify({"error": "Database error"}), 500

    if data is None:
        return jsonify({"error": "Not found"}), 404

    return jsonify(data)
