# AI-Job-Aggregator

Job aggregation + scoring/ranking against a user profile.

Planned:
- Ingest job listings from multiple sources (starting with public sources; no ToS-violating scraping).
- Normalize to a common schema.
- Score jobs against a candidate profile (skills, seniority, location/remote fit, keywords).
- Store in a DB and expose via CLI/API.

## Tech
- Python
- `uv` for dependency management

## Notes
This repo intentionally does **not** commit credentials, API keys, or generated dependency artifacts.
