"""
Unit tests for ExtractionService job-lifecycle / concurrency fixes (issue #1, P1):
- #1.1 TTL sweeper + cleanup_job artifact garbage collection
- #1.2 soft wall-clock timeout around process_pdf
- #1.3 double-run guard (JobConflictError on non-pending job)
"""

import threading
from datetime import datetime, timedelta

import pytest

import services.extraction_service as svc
from services.extraction_service import (
    ExtractionService,
    ProcessingJob,
    JobStatus,
    JobConflictError,
    ProcessingError,
)


@pytest.fixture
def service(tmp_path):
    """A service backed by isolated temp folders."""
    return ExtractionService(
        upload_folder=str(tmp_path / "uploads"),
        template_folder=str(tmp_path / "templates"),
        output_folder=str(tmp_path / "outputs"),
    )


def _make_job(service, job_id, status=JobStatus.COMPLETED, completed_at=None):
    """Create a job with on-disk upload folder, output files, and a record."""
    job = ProcessingJob(job_id, str(service.upload_folder))
    upload = job.job_folder / "input.pdf"
    upload.write_bytes(b"%PDF-1.4 fake")
    job.files_submitted = [upload]
    job.status = status
    job.completed_at = completed_at

    xlsx = service.output_folder / f"{job_id}_output.xlsx"
    xlsx.write_bytes(b"xlsx")
    csv = service.output_folder / f"{job_id}_output.csv"
    csv.write_text("csv")
    job.output_excel = xlsx
    job.output_csv = csv

    service.jobs[job_id] = job
    service._persist_job(job)
    return job


# ------------------------- #1.1 cleanup / sweeper -------------------------

class TestCleanupJob:
    def test_cleanup_removes_all_artifacts(self, service):
        job = _make_job(service, "job-clean", completed_at=datetime.utcnow())
        job_folder = job.job_folder
        xlsx = service.output_folder / "job-clean_output.xlsx"
        csv = service.output_folder / "job-clean_output.csv"
        record = service.jobs_dir / "job-clean.json"
        assert job_folder.exists() and xlsx.exists() and csv.exists() and record.exists()

        service.cleanup_job("job-clean")

        assert not job_folder.exists()
        assert not xlsx.exists()
        assert not csv.exists()
        assert not record.exists()
        assert "job-clean" not in service.jobs

    def test_cleanup_is_idempotent(self, service):
        _make_job(service, "job-twice", completed_at=datetime.utcnow())
        service.cleanup_job("job-twice")
        # Second call on already-gone artifacts must not raise.
        service.cleanup_job("job-twice")


class TestSweepExpiredJobs:
    def test_sweeps_only_old_terminal_jobs(self, service):
        now = datetime.utcnow()
        old = now - timedelta(hours=48)        # past 24h TTL
        recent = now - timedelta(hours=1)      # within TTL

        _make_job(service, "old-done", JobStatus.COMPLETED, completed_at=old)
        _make_job(service, "old-error", JobStatus.ERROR, completed_at=old)
        _make_job(service, "recent-done", JobStatus.COMPLETED, completed_at=recent)
        _make_job(service, "old-processing", JobStatus.PROCESSING, completed_at=None)
        _make_job(service, "old-pending", JobStatus.PENDING, completed_at=None)

        swept = service.sweep_expired_jobs(now=now)

        assert swept == 2
        assert not (service.jobs_dir / "old-done.json").exists()
        assert not (service.jobs_dir / "old-error.json").exists()
        # Recent and non-terminal jobs are preserved.
        assert (service.jobs_dir / "recent-done.json").exists()
        assert (service.jobs_dir / "old-processing.json").exists()
        assert (service.jobs_dir / "old-pending.json").exists()

    def test_sweeper_thread_start_is_idempotent(self, service):
        service._sweep_interval = 9999  # don't actually fire during the test
        service.start_cleanup_sweeper()
        first = service._sweeper_thread
        service.start_cleanup_sweeper()
        assert service._sweeper_thread is first
        assert first.is_alive()
        service.stop_cleanup_sweeper()


# ------------------------- #1.3 double-run guard -------------------------

class TestProcessJobGuard:
    @pytest.mark.parametrize(
        "status",
        [JobStatus.PROCESSING, JobStatus.COMPLETED, JobStatus.ERROR, JobStatus.CANCELLED],
    )
    def test_non_pending_job_raises_conflict(self, service, status):
        job = _make_job(service, f"job-{status.value}", status=status,
                        completed_at=datetime.utcnow())
        with pytest.raises(JobConflictError):
            service.process_job(job.job_id)
        # Status is untouched — the guard must not flip it to error.
        assert service.jobs[job.job_id].status == status

    def test_conflict_is_a_processing_error(self):
        # Route layer relies on subclassing for backwards-compatible handling.
        assert issubclass(JobConflictError, ProcessingError)


# ------------------------- #1.2 PDF timeout -------------------------

class TestPdfTimeout:
    def test_hung_pdf_times_out_and_errors_job(self, service, monkeypatch):
        release = threading.Event()

        def hang(_path):
            release.wait(5)  # released by the test once assertions pass
            return []

        monkeypatch.setattr(svc, "process_pdf", hang)
        service.pdf_timeout = 0.2

        job = ProcessingJob("job-timeout", str(service.upload_folder))
        pdf = job.job_folder / "slow.pdf"
        pdf.write_bytes(b"%PDF-1.4")
        job.files_submitted = [pdf]
        job.status = JobStatus.PENDING
        service.jobs[job.job_id] = job

        try:
            with pytest.raises(ProcessingError) as exc:
                service.process_job(job.job_id)
            assert "timed out" in str(exc.value).lower()
            assert service.jobs[job.job_id].status == JobStatus.ERROR
        finally:
            release.set()  # let the abandoned worker thread exit promptly
