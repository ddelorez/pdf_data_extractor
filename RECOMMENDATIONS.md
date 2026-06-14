# PDF Data Extractor — Remediation Checklist

A prioritized, reviewable list of issues found in an audit of the repo (Flask/Python
backend + React/Vite frontend, Dockerized, GitHub Actions CI). Each item has enough
context to evaluate independently. File:line references point at the offending code.

> Status legend: `[ ]` open · `[~]` in progress · `[x]` done
> Severity: 🔴 critical · 🟠 high · 🟡 medium · ⚪ low

---

## A. CI / build — currently red or silently misleading

- [ ] 🔴 **A1. CI installs from a `requirements.txt` that no longer exists.**
  The repo migrated to `uv` + `pyproject.toml`/`uv.lock`, but
  `.github/workflows/code-quality.yml:43,109,154` still run `pip install -r requirements.txt`,
  and `code-quality.yml:10,19` + `docker-build.yml:10` trigger on a `requirements.txt`
  path that no longer changes. The installs only "pass" because of `continue-on-error: true`,
  so lint/security scans run against **no installed dependencies** and report a false clean.
  **Fix:** replace with `uv sync` (or `pip install .`); update path filters to `pyproject.toml`/`uv.lock`.

- [ ] 🔴 **A2. Frontend unit tests assert a dead contract → CI fails.**
  `frontend/src/services/api.test.js:132,153` assert downloads hit
  `http://localhost:3001/download/...`, but the real client (`api.js:5`) uses `/api/download/...`.
  Port `3001` appears nowhere in the stack. `frontend-tests.yml` runs `test:run` without
  `continue-on-error`, so this job fails.
  **Fix:** update assertions to `/api/download/<jobId>/output.{xlsx,csv}`.

- [ ] 🔴 **A3. Missing `frontend/package-lock.json`.**
  CI sets `cache: 'npm'` with `cache-dependency-path: frontend/package-lock.json` (file absent)
  and uses `npm install` (non-reproducible) instead of `npm ci`.
  **Fix:** commit a lockfile; switch CI to `npm ci`.

- [ ] ⚪ **A4. Deprecated CI actions.** `actions/upload-artifact@v3`, `codecov-action@v3`,
  `github-script@v6`, `setup-python@v4` are old majors (v3 artifact is being retired).
  **Fix:** bump to v4/v5/v7 as applicable.

- [ ] ⚪ **A5. Linting never gates merges.** Lint/format steps use `continue-on-error: true`
  everywhere; flake8 uses `--max-line-length=127` while Black uses 88 (they disagree).
  **Fix:** align line length; drop `continue-on-error` on core lint/test steps once green.

---

## B. Docker images / vulnerabilities

- [ ] 🟠 **B1. `node:18-alpine` build base is end-of-life.** (`frontend/Dockerfile:2`)
  Node 18 left active support; no further security patches. This is the biggest concrete
  image-CVE lever.
  **Fix:** bump to `node:20-alpine` or `node:22-alpine`; rebuild and re-test the frontend.

- [ ] 🟠 **B2. Base images are unpinned (tag-only, no digest).**
  `python:3.11-slim` (`Dockerfile:5,21`), `nginx:alpine` (`frontend/Dockerfile:19`),
  `node:18-alpine` (`frontend/Dockerfile:2`), `uv:0.5` (`Dockerfile:7`). Tag-only pins drift
  and make builds non-reproducible; stale local layers also hide OS-package CVE fixes.
  **Fix:** pin by digest (`@sha256:...`) and establish a periodic rebuild so OS patches land.

- [ ] 🟡 **B3. No image vulnerability scanning in CI.**
  Nothing scans the built images for CVEs.
  **Fix:** add a Trivy (or Grype) scan step to `docker-build.yml`; fail on HIGH/CRITICAL with
  an allowlist for accepted findings.

- [ ] 🟡 **B4. Frontend healthcheck reliability + port mismatch.**
  `frontend/Dockerfile:52` healthchecks with `wget --spider` (verify it exists in the chosen
  nginx base); `docker-compose.yml:92` publishes `80:3000` while `docker-build.yml:73` smoke-tests
  port `3000` on the host (only saved by `continue-on-error`).
  **Fix:** confirm the probe tool is present (or use `curl`); make the CI smoke test hit the
  published port (`:80`).

- [ ] ⚪ **B5. Rebuild OS packages on each build.** `python:3.11-slim` runtime installs `curl`/`gosu`
  via apt without an `apt-get upgrade` and may run on cached base layers. Periodic clean rebuilds
  (B2) plus scanning (B3) address most slim-image CVEs.

---

## C. Security — request boundary & config

- [ ] 🟠 **C1. `job_id` not validated → path-traversal surface.**
  `job_id` flows from the URL into `jobs_dir / f"{job_id}.json"` and `upload_folder / job_id`
  (which `mkdir`s), e.g. `services/extraction_service.py` `_load_job` / `ProcessingJob.__init__`.
  A crafted `job_id` (`../../...`) escapes the base dir.
  **Fix:** validate against a UUID regex (`^[0-9a-f-]{36}$`) at the route boundary before any FS use.

- [ ] 🟠 **C2. Upload validation is extension-only.**
  `secure_filename` is imported (`routes/extraction.py:7`) but unused; only `.pdf` suffix is
  checked (`extraction_service.py:349-368`). Any non-PDF renamed `.pdf` reaches `pdfplumber`.
  **Fix:** verify the `%PDF-` magic header after save; enforce a per-file size limit (not just
  the aggregate `MAX_CONTENT_LENGTH`).

- [ ] 🟠 **C3. Wildcard CORS in two layers.**
  Both `frontend/nginx.conf:30-32` and Flask `CORS(app)` (`app.py:78-80`, default `CORS_ORIGINS=*`)
  emit `Access-Control-Allow-Origin: *`. The SPA and API are same-origin behind nginx, so this is
  unnecessary and can produce a duplicate ACAO header that browsers reject.
  **Fix:** remove CORS headers from nginx; set `CORS_ORIGINS` to the deployed origin (no `*` default).

- [ ] 🟡 **C4. Weak default `SECRET_KEY`.**
  Falls back to `'dev-key-not-for-production'` (`app.py:51`); compose default is a placeholder.
  **Fix:** fail startup if unset when `FLASK_ENV=production`.

- [ ] 🟡 **C5. Error responses leak internals.**
  500s return `"details": str(e)` (`routes/extraction.py:108,167`; `extraction_service.py:578-585`),
  exposing exception text/paths.
  **Fix:** log details server-side; return a generic message to clients.

---

## D. Backend correctness / concurrency

- [ ] 🟠 **D1. Data races + double-processing in the job model.**
  Gunicorn runs `--workers 1 --threads 4` (in-process threads). `self._lock` guards only
  `self.jobs` dict membership; `process_job` mutates `job.records_extracted`/`files_processed`
  outside the lock while `get_status_dict()` reads them. Separately, `submit_files` auto-starts
  a background processing thread *and* `POST /api/process/<job_id>` can trigger processing again,
  with no guard against re-processing a `PROCESSING`/`COMPLETED` job → double-write of outputs and
  corrupted counters. (`extraction_service.py:374-388,413-445`; `routes/extraction.py:141`)
  **Fix:** refuse to (re)process a non-pending job; mutate job fields under the lock; consider a
  real task queue if scaling beyond one worker.

- [ ] 🟡 **D2. `request.json.get()` can 500.**
  `routes/extraction.py:139`: an empty/`null` JSON body makes `request.json` `None`, so `.get()`
  raises → generic 500.
  **Fix:** `request.get_json(silent=True) or {}`.

- [ ] 🟡 **D3. No job cleanup → unbounded growth.**
  `ProcessingJob.cleanup()` (`extraction_service.py:167-174`) is never called; uploads, outputs,
  and `jobs/*.json` accumulate forever and all reload into memory at startup.
  **Fix:** add TTL-based cleanup; cap reloaded jobs.

- [ ] 🟡 **D4. Internal `_format` column leaks into SOR CSV.**
  Flowback writers strip `_format`, but the SOR path's `write_csv` (`src/output/csv_writer.py:48`)
  dumps every column including `_format`.
  **Fix:** drop non-expected columns before CSV write.

- [ ] 🟡 **D5. Mixed-format batches fail late.**
  Format is inferred from `_format` tags *after* extracting all PDFs; a mixed SOR+flowback batch
  errors out after doing all the work, and a missing `_format` silently assumes `narrative_sor`
  (`extraction_service.py:471-477`).
  **Fix:** detect format per file at submit time; reject mixed batches early.

- [ ] ⚪ **D6. `datetime.utcnow()` deprecated** (`extraction_service.py:74,108,116`;
  `routes/extraction.py:43`). **Fix:** `datetime.now(datetime.UTC)`.

- [ ] ⚪ **D7. Extraction regex bugs reducing accuracy.**
  `src/config.py:100` `WELL_NAME_PATTERNS[0]` has stray literal spaces inside the capture group
  (`( [A-Z0-9\s\-]{8,40} )`) that break common headers; `src/core/extraction.py:244` choke regex
  `(?:on|choke)` matches "on" inside other words.
  **Fix:** remove literal spaces + `.strip()`; anchor with word boundaries. (Validate against real PDFs.)

- [ ] ⚪ **D8. `config.py` makes directories at import time** (`src/config.py:19-20`), which can crash
  imports on a read-only FS. **Fix:** wrap in try/except or move into an init function.

---

## E. Frontend correctness

- [ ] 🟡 **E1. `cancelled` status unhandled.**
  `usePolling.js:30` stops on `completed|failed|error` but not `cancelled`, so a cancelled job
  polls forever; `App.jsx:105-116` leaves `appState` stuck at `processing`.
  **Fix:** add `'cancelled'` to terminal checks and reset App to idle.

- [ ] 🟡 **E2. In-batch duplicate detection uses the wrong array.**
  `useFileUpload.js` `validateFiles` checks duplicates against `files` (post-upload, empty until
  after an upload) instead of `selectedFiles` (pending), so same-file dupes slip through in one batch.
  **Fix:** compare against `selectedFiles`.

- [ ] 🟡 **E3. Download path documented inconsistently.**
  `api.js` is correct (`/api/download`), but `app.py:176-181` `/api/docs`, `mockResponses.js:16-17`,
  and the `vite.config.js` proxy advertise/proxy a bare `/download` the backend never serves.
  **Fix:** standardize everything on `/api/download`.

- [ ] 🟡 **E4. File-size limits inconsistent.**
  Frontend rejects >50 MB *per file* (`useFileUpload.js:4`); nginx + Flask allow 100 MB *total body*.
  Three 40 MB PDFs pass the client but get a raw 413.
  **Fix:** align limits; validate aggregate size client-side and surface 413 cleanly.

- [ ] ⚪ **E5. Double-start of polling on retry.**
  `App.jsx` `handleErrorRetry` calls `startPolling()` while `ProcessingStatus` also auto-starts it
  via `useEffect`, causing redundant requests.
  **Fix:** guard `startPolling` with `if (isPolling) return;` and use a single trigger path.

- [ ] ⚪ **E6. Dead/misleading API surface.**
  `processJob` (`api.js:60-67`) and `POST /api/process` are unused (backend auto-processes on upload)
  but still exported, tested, and documented; `/process` returns `unique_wells` while `/status`
  returns `wells`/`records` aliases.
  **Fix:** remove or clearly mark as manual; align field names across endpoints.

- [ ] 🟡 **E7. Unresolved npm audit findings in frontend dependencies.**
  Lockfile generation (and the existing non-gating `npm audit --audit-level=moderate || true` step in
  `code-quality.yml`) surfaced 8 vulnerabilities (3 critical, 2 high, 1 moderate, 2 low) plus multiple
  deprecated packages (eslint@8.57.1, rimraf@3.0.2, inflight@1.0.6, glob@7.2.3, @humanwhocodes/*, etc.).
  **Fix:** Triage critical/high first. Apply `npm audit fix` for safe resolutions; perform major bumps
  (e.g. eslint 8→9) where needed and validate via lint/tests/build. Document auto-fixable items vs.
  those requiring manual changes or risk acceptance. Consider making the CI audit step gating once
  the tree is clean. Owned by the Frontend track.

---

## Suggested order of execution

1. **Unblock CI** — A1, A2, A3 (mechanical; currently red/misleading).
2. **Image vulnerabilities** — B1, B2, B3 (the user's explicit priority).
3. **Request-boundary hardening** — C1, C2, C3 (small, high-value, independently testable).
4. **Concurrency rework** — D1 (highest correctness risk; needs care — do as its own change).
5. **Cleanup & polish** — remaining D/E items, A4/A5.

> Items deliberately *excluded* as non-issues after verification: "Flask dev server in production"
> (the Dockerfile correctly runs gunicorn; only the local `main()` path uses `app.run`).
