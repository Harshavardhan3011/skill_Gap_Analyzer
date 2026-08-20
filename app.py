"""
SkillGap Analyzer — Flask application entry point.

Run with:
    python app.py

Or with Flask CLI:
    set FLASK_APP=app.py
    flask run
"""

import logging
import os
import sys

# ── Ensure project root is on the import path ─────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask

from config.settings import SECRET_KEY, DEBUG, MAX_CONTENT_LENGTH
from database.database import init_db
from routes.main_routes import main_bp
from routes.analysis_routes import analysis_bp

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """
    Application factory.

    Returns a fully configured Flask application instance.
    Using a factory makes the app easier to test.
    """
    app = Flask(__name__)

    # ── Configuration ─────────────────────────────────────────────────────────
    app.secret_key = SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    app.config["DEBUG"] = DEBUG

    # ── Database initialization ───────────────────────────────────────────────
    init_db()

    # ── Blueprints ────────────────────────────────────────────────────────────
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)

    # ── Global error handlers ─────────────────────────────────────────────────
    from flask import render_template

    @app.errorhandler(404)
    def not_found(exc):
        return render_template(
            "error.html", error_code=404, error_message="Page not found."
        ), 404

    @app.errorhandler(413)
    def request_too_large(exc):
        return render_template(
            "error.html",
            error_code=413,
            error_message="Uploaded file is too large. Maximum allowed size is 2 MB.",
        ), 413

    @app.errorhandler(500)
    def server_error(exc):
        logger.error("500 error: %s", exc, exc_info=True)
        return render_template(
            "error.html", error_code=500, error_message="An internal error occurred."
        ), 500

    logger.info("SkillGap Analyzer started. Debug=%s", DEBUG)
    return app


# ── Module-level instance ─────────────────────────────────────────────────────
# Must be at module scope so Vercel (and any WSGI server) can discover `app`
# when it imports this file directly (rather than running it as a script).
app = create_app()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=DEBUG)
