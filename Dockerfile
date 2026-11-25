
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src

# ---------- Test: runs pytest + ruff ----------
FROM base AS test
COPY tests ./tests
RUN pip install -e ".[dev]"
CMD ["sh", "-c", "pytest && ruff check ."]

# ---------- Runtime: runs the reviewer ----------
FROM base AS runtime
RUN pip install . && useradd --create-home appuser
USER appuser
ENTRYPOINT ["python", "-m", "ai_reviewer"]