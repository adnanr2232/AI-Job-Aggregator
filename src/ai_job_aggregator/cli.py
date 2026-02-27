from __future__ import annotations

import argparse
import logging

from ai_job_aggregator.db import create_engine_from_settings, create_session_factory
from ai_job_aggregator.logging import configure_logging
from ai_job_aggregator.settings import Settings

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-job-aggregator",
        description="AI Job Aggregator",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    parser.add_argument("--log-level", default="INFO", help="Log level (default: INFO)")

    sub = parser.add_subparsers(dest="cmd", required=False)

    ingest = sub.add_parser("ingest", help="Run ingestion")
    ingest.add_argument(
        "--source",
        default="remoteok",
        choices=["remoteok"],
        help="Connector source (default: remoteok)",
    )
    ingest.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max items to fetch from the connector for this run (clamped to hard cap)",
    )
    ingest.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Candidate profile selector (id or label); stored on ingestion_run",
    )

    sub.add_parser("db-init", help="Create tables directly (dev convenience; prefer alembic)")

    sub.add_parser("worker", help="Run RQ worker (listens on scoring queue)")

    score = sub.add_parser("score", help="Run scoring synchronously for a scoring run")
    score.add_argument("--run-id", type=int, required=True, help="Scoring run id")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        from importlib.metadata import version

        print(version("ai-job-aggregator"))
        return 0

    configure_logging(args.log_level)

    settings = Settings()
    engine = create_engine_from_settings(settings)
    SessionFactory = create_session_factory(engine)

    if args.cmd == "db-init":
        from ai_job_aggregator.models import Base

        Base.metadata.create_all(engine)
        logger.info(
            "db_initialized",
            extra={
                "db_path": str(settings.resolved_db_path()),
                "storage_dir": str(settings.storage_dir),
            },
        )
        return 0

    if args.cmd == "ingest":
        from ai_job_aggregator.connectors.remoteok import RemoteOkConnector
        from ai_job_aggregator.ingest import run_ingestion

        connector = RemoteOkConnector(settings)
        with SessionFactory() as session:
            return run_ingestion(
                session=session,
                connector=connector,
                limit=args.limit,
                profile_selector=args.profile,
            )

    if args.cmd == "worker":
        from ai_job_aggregator.worker import run_worker

        run_worker()
        return 0

    if args.cmd == "score":
        from ai_job_aggregator.scoring.service import score_run

        with SessionFactory() as session:
            score_run(session=session, run_id=args.run_id)
        return 0

    parser.print_help()
    return 0
