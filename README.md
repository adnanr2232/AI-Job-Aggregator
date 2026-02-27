# AI Job Aggregator

Bootstrap scaffold for a Python CLI + package.

## Quickstart

```bash
uv sync --dev

# Initialize your local DB (stored under `AJA_STORAGE_DIR`)
uv run ai-job-aggregator db-init

# (dev) start redis for async scoring
# docker compose -f docker-compose.redis.yml up -d

# (dev) start the scoring worker
# uv run ai-job-aggregator worker

# Ingest from RemoteOK (public JSON API)
uv run ai-job-aggregator ingest --source remoteok

# limit ingestion per run
uv run ai-job-aggregator ingest --source remoteok --limit 50

# optional: pick a candidate profile by id or label.
# If provided, ingestion will enqueue an async scoring run (if redis is available)
uv run ai-job-aggregator ingest --profile default

# manual scoring (sync)
uv run ai-job-aggregator score --run-id 1
```

### Configuration

Environment variables (prefix: `AJA_`):

- `AJA_STORAGE_DIR` (defaults to a local directory; set it to whatever you want)
- `AJA_DB_PATH` (optional override; otherwise `${AJA_STORAGE_DIR}/data/jobs.sqlite3`)
- `AJA_REMOTEOK_URL` (default: `https://remoteok.com/api`)
- `AJA_MAX_FETCH_PER_CONNECTOR` (default: `50`, hard cap: `100`)
- `AJA_REDIS_URL` (default: `redis://localhost:6379/0`)

Example:

```bash
AJA_STORAGE_DIR=/tmp/job-aggregator uv run ai-job-aggregator db-init
AJA_STORAGE_DIR=/tmp/job-aggregator uv run ai-job-aggregator ingest

# optional: pick a candidate profile by id or label
AJA_STORAGE_DIR=/tmp/job-aggregator uv run ai-job-aggregator ingest --profile default
```

### Notes

RemoteOK returns a `legal`/metadata row as the first element; the connector skips it and ingests the job items.

## Dev tooling

```bash
uv run ruff check .
uv run ruff format .
uv run pyright
uv run mypy .
uv run pre-commit run -a
```
