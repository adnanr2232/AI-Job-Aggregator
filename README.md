# AI Job Aggregator

Bootstrap scaffold for a Python CLI + package.

## Quickstart

```bash
uv sync --dev

# Initialize your local DB (stored in ~/Desktop/job-aggregator by default)
uv run ai-job-aggregator db-init

# Ingest from RemoteOK (public JSON API)
uv run ai-job-aggregator ingest --source remoteok
```

### Configuration

Environment variables (prefix: `AJA_`):

- `AJA_STORAGE_DIR` (default: `~/Desktop/job-aggregator`)
- `AJA_DB_PATH` (optional override; otherwise `${AJA_STORAGE_DIR}/data/jobs.sqlite3`)
- `AJA_REMOTEOK_URL` (default: `https://remoteok.com/api`)

Example:

```bash
AJA_STORAGE_DIR=/tmp/job-aggregator uv run ai-job-aggregator db-init
AJA_STORAGE_DIR=/tmp/job-aggregator uv run ai-job-aggregator ingest
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
