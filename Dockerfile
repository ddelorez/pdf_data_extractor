# Multi-stage Docker build for PDF Extractor API
# Production-ready Flask application with gunicorn

# Stage 1: Builder - Install dependencies with uv
FROM python:3.11-slim@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca AS builder

COPY --from=ghcr.io/astral-sh/uv@sha256:7bff3c3776ec467fc1437960f2c469d8beb30f536a6465a3350c647ccd260ec2 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install dependencies into /app/.venv from the lockfile (no dev deps).
# WORKDIR must match the runtime path so uv-generated console scripts
# (e.g. gunicorn) get the correct absolute shebang to /app/.venv/bin/python.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    FLASK_DEBUG=0 \
    PATH=/app/.venv/bin:$PATH

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Install curl for healthcheck (B5: upgrade base packages for security patches on each build)
RUN apt-get update && apt-get upgrade -y --no-install-recommends && apt-get install -y --no-install-recommends curl gosu && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the prebuilt virtualenv from the builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser . .

# Create required directories with proper permissions
RUN mkdir -p uploads outputs templates logs && \
    chown -R appuser:appuser /app

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Production WSGI server with gunicorn
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "1", \
     "--threads", "4", \
     "--worker-class", "gthread", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "app:create_app()"]
