# Agent Notes (AI-Job-Aggregator)

This file is for continuity across sessions.

## Repo
- GitHub: https://github.com/adnanr2232/AI-Job-Aggregator
- Local path (OpenClaw workspace): `${OPENCLAW_HOME}/workspace/AI-Job-Aggregator`
  - Example (this machine): `/home/slowgamer/.openclaw/workspace/AI-Job-Aggregator`

## Goals
- Aggregate jobs from multiple sources (start with official/public feeds and APIs; avoid ToS-violating scraping).
- Support multiple candidate profiles; profiles should be flexible (semi-structured) so we can evolve fields.
- Score jobs vs profile (heuristics now; later AI-assisted scoring).
- Store jobs + ingestion traces in DB; offer CLI and API (FastAPI later) + frontend later.

## Current implementation (vertical slice)
### Stack
- Python + `uv`
- SQLite for now
- SQLAlchemy 2 ORM
- Alembic migrations
- Pydantic models separated from DB models
- Structured JSON logs

### Connector implemented
- `RemoteOkConnector` (RemoteOK official JSON API: `https://remoteok.com/api`)
  - Requires a User-Agent header to avoid 403.
  - First element is metadata/legal; connector skips it.

### DB schema (initial)
- `job_postings`
  - Includes extracted fields plus `raw` JSON for additional/unmodeled fields.
  - Dedup strategy: `(source, source_item_id)` unique-ish behavior in ingestion (mark duplicates as `skipped`).
- Ingestion tracing tables
  - `ingestion_runs`: run-level status + meta JSON
  - `ingestion_items`: per-item status, raw payload JSON, optional link to `job_postings`
  - `ingestion_errors`: error type/message/traceback + JSON data (per-item)

### Settings
- `AJA_` env prefix (pydantic-settings)
- Storage dir default: `~/Desktop/job-aggregator`
- DB default: `${storage_dir}/data/jobs.sqlite3`

## How to run
```bash
cd ${OPENCLAW_HOME}/workspace/AI-Job-Aggregator
uv sync --dev

# initialize DB
aI-job-aggregator db-init

# ingest RemoteOK
ai-job-aggregator ingest --source remoteok
```

(You can override storage dir)
```bash
AJA_STORAGE_DIR=/tmp/job-aggregator ai-job-aggregator db-init
AJA_STORAGE_DIR=/tmp/job-aggregator ai-job-aggregator ingest --source remoteok
```

## Logging approach
- Normal app logs: JSON structured logs to stdout (good for later piping to files/ELK).
- Ingestion debugability: persisted in DB via ingestion_* tables with per-item outcomes and detailed errors.

## Near-term next steps
- Add DB init via Alembic (preferred) and ensure CLI uses migrations.
- Add basic heuristic scoring fields + scoring table (job_id, profile_id, score, reasons JSON).
- Add candidate profiles table (semi-structured JSON + extracted fields).
- Add filters: remote-only, keywords, seniority etc.
- Add a simple FastAPI read-only endpoint to list jobs and ingestion runs.
