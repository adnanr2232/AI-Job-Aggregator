# AI Job Aggregator

Bootstrap scaffold for a Python CLI + package.

## Quickstart

```bash
uv sync --dev

# Initialize your local DB (stored under `AJA_STORAGE_DIR`)
uv run ai-job-aggregator db-init

# Ingest from RemoteOK (public JSON API)
uv run ai-job-aggregator ingest --source remoteok

# limit ingestion per run
uv run ai-job-aggregator ingest --source remoteok --limit 50
```

### Configuration

Environment variables (prefix: `AJA_`):

- `AJA_STORAGE_DIR` (defaults to a local directory; set it to whatever you want)
- `AJA_DB_PATH` (optional override; otherwise `${AJA_STORAGE_DIR}/data/jobs.sqlite3`)
- `AJA_REMOTEOK_URL` (default: `https://remoteok.com/api`)
- `AJA_MAX_FETCH_PER_CONNECTOR` (default: `50`, hard cap: `100`)

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
