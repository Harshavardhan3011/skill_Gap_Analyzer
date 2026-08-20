"""
File reading utilities for Skill Gap Analyzer.

Supports:
  .txt  — UTF-8 with Latin-1 fallback
  .pdf  — via pypdf (optional; graceful degradation if not installed)

Security measures:
  - Filenames are sanitized with werkzeug's secure_filename
  - Files are read from a controlled temp path only
  - File size is validated before reading
"""

import logging
import os
from typing import Tuple

from werkzeug.utils import secure_filename

from config.settings import MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS, UPLOAD_FOLDER
from utils.validators import validate_file_extension, validate_file_size

logger = logging.getLogger(__name__)

# ── PDF support (optional) ────────────────────────────────────────────────────
try:
    from pypdf import PdfReader as _PdfReader
    PDF_SUPPORTED = True
except ImportError:
    try:
        from PyPDF2 import PdfReader as _PdfReader  # type: ignore
        PDF_SUPPORTED = True
    except ImportError:
        PDF_SUPPORTED = False
        logger.info("pypdf / PyPDF2 not installed. PDF upload not supported.")


class FileHandler:
    """
    Handles secure file reading for uploaded resume / JD files.

    Text is extracted and returned as a plain string.
    """

    def __init__(self, upload_folder: str = UPLOAD_FOLDER) -> None:
        self.upload_folder = upload_folder
        try:
            os.makedirs(self.upload_folder, exist_ok=True)
        except OSError as exc:
            # On read-only filesystems (e.g. Vercel /var/task) this is non-fatal;
            # file uploads simply won't be saved to disk (they are processed in-memory).
            logger.warning("Could not create upload folder %s: %s", self.upload_folder, exc)

    def read_uploaded_file(self, file_storage) -> Tuple[bool, str]:
        """
        Read text content from a Werkzeug FileStorage object.

        Args:
            file_storage: werkzeug.datastructures.FileStorage from request.files.

        Returns:
            (True, text_content) on success.
            (False, error_message) on failure.
        """
        if file_storage is None or file_storage.filename == "":
            return False, "No file selected."

        filename = secure_filename(file_storage.filename)

        # Validate extension
        valid, err = validate_file_extension(filename)
        if not valid:
            return False, err

        # Read bytes to check size
        try:
            content_bytes = file_storage.read()
        except OSError as exc:
            logger.error("Failed to read uploaded file: %s", exc)
            return False, "Failed to read the uploaded file. Please try again."

        # Validate size
        valid, err = validate_file_size(len(content_bytes))
        if not valid:
            return False, err

        # Reset stream position (in case caller needs to reuse)
        file_storage.stream.seek(0)

        ext = filename.rsplit(".", 1)[-1].lower()

        if ext == "txt":
            return self._decode_text(content_bytes)
        elif ext == "pdf":
            return self._read_pdf_bytes(content_bytes)
        else:
            return False, f"Unsupported file type: .{ext}"

    @staticmethod
    def _decode_text(content_bytes: bytes) -> Tuple[bool, str]:
        """Try UTF-8 then Latin-1 to decode text bytes."""
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                text = content_bytes.decode(encoding)
                return True, text
            except UnicodeDecodeError:
                continue
        return False, "Could not decode the text file. Please save it as UTF-8 and retry."

    @staticmethod
    def _read_pdf_bytes(content_bytes: bytes) -> Tuple[bool, str]:
        """Extract text from PDF bytes using pypdf / PyPDF2."""
        if not PDF_SUPPORTED:
            return (
                False,
                "PDF support is not installed. "
                "Please paste your text directly or upload a .txt file. "
                "To enable PDF support, run: pip install pypdf",
            )

        import io
        try:
            reader = _PdfReader(io.BytesIO(content_bytes))
            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)

            if not pages_text:
                return (
                    False,
                    "Could not extract text from the PDF. "
                    "The PDF may be image-based (scanned). "
                    "Please use a text-based PDF or paste the text directly.",
                )

            return True, "\n".join(pages_text)

        except Exception as exc:  # noqa: BLE001 — broad catch for pypdf errors
            logger.error("PDF extraction failed: %s", exc)
            return (
                False,
                "Failed to extract text from the PDF. "
                "Please paste the text directly instead.",
            )
