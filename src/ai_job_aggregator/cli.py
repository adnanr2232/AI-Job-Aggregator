from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-job-aggregator",
        description="AI Job Aggregator (bootstrap CLI)",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        # Avoid importing package metadata until needed.
        from importlib.metadata import version

        print(version("ai-job-aggregator"))
        return 0

    print("AI Job Aggregator: CLI scaffold ready. Implement commands in ai_job_aggregator/cli.py")
    return 0
