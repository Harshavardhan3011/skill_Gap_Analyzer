"""
Main routes — home page and static informational views.
"""

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Home / landing page."""
    return render_template("index.html")


@main_bp.errorhandler(404)
def page_not_found(exc):
    return render_template("error.html", error_code=404,
                           error_message="Page not found."), 404


@main_bp.errorhandler(500)
def internal_error(exc):
    return render_template("error.html", error_code=500,
                           error_message="An internal error occurred."), 500
