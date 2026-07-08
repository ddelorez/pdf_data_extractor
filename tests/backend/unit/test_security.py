"""
Unit tests for P2 security hardening (issue #1):
- #1.6  SECRET_KEY fail-fast in production
- #1.15 magic-byte (%PDF-) upload validation
- job_id UUID validation (route layer)
"""

import io
import tempfile

import pytest
from werkzeug.datastructures import FileStorage

from app import resolve_secret_key, create_app
from services.extraction_service import (
    ExtractionService,
    FileValidationError,
    NonPdfFileError,
    _looks_like_pdf,
)
from routes.extraction import validate_job_id


# ------------------------- #1.6 SECRET_KEY -------------------------

class TestResolveSecretKey:
    def test_production_missing_key_raises(self, monkeypatch):
        monkeypatch.setenv("FLASK_ENV", "production")
        monkeypatch.delenv("SECRET_KEY", raising=False)
        with pytest.raises(RuntimeError):
            resolve_secret_key()

    @pytest.mark.parametrize(
        "bad", ["dev-key-not-for-production", "your-secure-secret-key-here", "change-me", ""]
    )
    def test_production_insecure_key_raises(self, monkeypatch, bad):
        monkeypatch.setenv("FLASK_ENV", "production")
        monkeypatch.setenv("SECRET_KEY", bad)
        with pytest.raises(RuntimeError):
            resolve_secret_key()

    def test_production_secure_key_passes(self, monkeypatch):
        monkeypatch.setenv("FLASK_ENV", "production")
        monkeypatch.setenv("SECRET_KEY", "a-proper-32-char-random-secret-value")
        assert resolve_secret_key() == "a-proper-32-char-random-secret-value"

    def test_testing_bypasses_production_guard(self, monkeypatch):
        monkeypatch.setenv("FLASK_ENV", "production")
        monkeypatch.delenv("SECRET_KEY", raising=False)
        # Exempt under TESTING so the suite runs without configuration.
        assert resolve_secret_key(testing=True)

    def test_non_production_uses_dev_fallback(self, monkeypatch):
        monkeypatch.setenv("FLASK_ENV", "development")
        monkeypatch.delenv("SECRET_KEY", raising=False)
        assert resolve_secret_key() == "dev-key-not-for-production"

    def test_create_app_fails_fast_in_production(self, monkeypatch):
        monkeypatch.setenv("FLASK_ENV", "production")
        monkeypatch.delenv("SECRET_KEY", raising=False)
        # No TESTING override -> guard active -> refuses to construct the app.
        with pytest.raises(RuntimeError):
            create_app()

    def test_create_app_testing_config_ok_in_production(self, monkeypatch):
        monkeypatch.setenv("FLASK_ENV", "production")
        monkeypatch.delenv("SECRET_KEY", raising=False)
        tmp = tempfile.mkdtemp()
        app = create_app(config={
            "TESTING": True,
            "UPLOAD_FOLDER": tmp,
            "OUTPUT_FOLDER": tmp,
            "TEMPLATE_FOLDER": tmp,
        })
        assert app is not None


# ------------------------- #1.15 magic-byte validation -------------------------

class TestLooksLikePdf:
    def test_real_pdf_header(self):
        assert _looks_like_pdf(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3")

    def test_marker_within_first_kb(self):
        assert _looks_like_pdf(b"\xef\xbb\xbf   %PDF-1.4 rest")

    def test_non_pdf_rejected(self):
        assert not _looks_like_pdf(b"PK\x03\x04 this is a zip / docx")
        assert not _looks_like_pdf(b"<html>not a pdf</html>")

    def test_marker_after_1kb_rejected(self):
        assert not _looks_like_pdf(b"x" * 2000 + b"%PDF-1.4")


class TestSubmitFilesMagicBytes:
    @pytest.fixture
    def service(self, tmp_path):
        return ExtractionService(
            upload_folder=str(tmp_path / "uploads"),
            template_folder=str(tmp_path / "templates"),
            output_folder=str(tmp_path / "outputs"),
        )

    def test_pdf_extension_but_not_pdf_content_rejected(self, service):
        fake = FileStorage(
            stream=io.BytesIO(b"This is plainly not a PDF document."),
            filename="malicious.pdf",
            content_type="application/pdf",
        )
        # NonPdfFileError (subclass of FileValidationError) -> route maps to 418
        with pytest.raises(NonPdfFileError, match="not a valid PDF"):
            service.submit_files([fake])

    def test_non_pdf_extension_rejected(self, service):
        fake = FileStorage(
            stream=io.BytesIO(b"%PDF-1.7 real pdf bytes but wrong name"),
            filename="notes.txt",
            content_type="text/plain",
        )
        with pytest.raises(NonPdfFileError, match="Invalid file type"):
            service.submit_files([fake])


# ------------------------- job_id UUID validation -------------------------

class TestValidateJobId:
    def test_valid_uuid_canonicalized(self):
        assert validate_job_id("22222222-2222-2222-2222-222222222222") == \
            "22222222-2222-2222-2222-222222222222"

    @pytest.mark.parametrize("bad", [
        "not-a-uuid", "test-123", "../../etc/passwd", "", "12345",
        "22222222-2222-2222-2222-22222222222z",
    ])
    def test_malformed_rejected(self, bad):
        with pytest.raises(ValueError):
            validate_job_id(bad)
