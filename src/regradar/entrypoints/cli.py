import argparse
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import httpx
import pydantic
import structlog

from regradar.adapters.dip.dip_procedure_source import (
    API_BASE_URL,
    DipProcedureSource,
    RetryPolicy,
)
from regradar.adapters.dip.rate_limit import RateLimiter
from regradar.adapters.jsonl_dead_letter_store import JsonlDeadLetterStore
from regradar.adapters.jsonl_raw_store import JsonlRawStore
from regradar.core.application.errors import ConfigurationError, SystemicError
from regradar.core.application.ingest import (
    IngestDependencies,
    RunSummary,
    ingest,
)
from regradar.core.domain.window import Window
from regradar.entrypoints.logging_config import configure_logging
from regradar.entrypoints.settings import Settings

log = structlog.get_logger()

EXIT_OK = 0
EXIT_RUN_FAILED = 1
EXIT_ABORTED = 2
DIP_MIN_INTERVAL_SECONDS = 1.0
HTTP_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class Paths:
    raw_dir: Path = Path("data/raw")
    dead_letters: Path = Path("data/raw/dead_letters.jsonl")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    window = _window(parser, args, date.today())
    configure_logging()
    try:
        return ingest_dip(window, refresh=args.refresh, paths=Paths())
    except SystemicError:
        log.exception("run_aborted")
        return EXIT_ABORTED


def ingest_dip(
    window: Window,
    *,
    refresh: bool,
    paths: Paths,
    transport: httpx.BaseTransport | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    with httpx.Client(
        base_url=API_BASE_URL,
        timeout=HTTP_TIMEOUT_SECONDS,
        transport=transport,
    ) as client:
        source = DipProcedureSource(
            client,
            _api_key(),
            RateLimiter(DIP_MIN_INTERVAL_SECONDS, sleep=sleep),
            RetryPolicy(sleep=sleep),
        )
        deps = IngestDependencies(
            source=source,
            raw_store=JsonlRawStore(paths.raw_dir, "dip_procedure"),
            dead_letters=JsonlDeadLetterStore(paths.dead_letters),
        )
        result = ingest(window, deps, refresh=refresh)
    return _finish(result.summary)


def _api_key() -> str:
    try:
        return Settings().dip_api_key.get_secret_value()
    except pydantic.ValidationError as err:
        msg = "DIP_API_KEY is not set (see .env.example)"
        raise ConfigurationError(msg) from err


def _finish(summary: RunSummary) -> int:
    log.info(
        "run_summary",
        loaded=summary.loaded,
        stored=summary.stored,
        discarded=summary.discarded,
        failed=summary.failed,
        failure_rate=round(summary.failure_rate, 4),
    )
    if not summary.reconciles:
        log.error("run_does_not_reconcile")
        return EXIT_RUN_FAILED
    if not summary.succeeded:
        log.error("failure_rate_exceeded")
        return EXIT_RUN_FAILED
    if summary.failed:
        log.warning("documents_failed", failed=summary.failed)
    return EXIT_OK


def _window(
    parser: argparse.ArgumentParser, args: argparse.Namespace, today: date
) -> Window:
    if args.months is not None:
        if args.end is not None:
            parser.error("--end requires --start, not --months")
        return Window.last_months(today, args.months)
    if args.end is None:
        parser.error("--start requires --end")
    if args.start > args.end:
        parser.error("--start must not be after --end")
    return Window(start=args.start, end=args.end)


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        msg = f"must be at least 1, got {number}"
        raise argparse.ArgumentTypeError(msg)
    return number


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="regradar")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest_cmd = commands.add_parser(
        "ingest-dip", help="Fetch DIP procedures and store the raw data"
    )
    span = ingest_cmd.add_mutually_exclusive_group(required=True)
    span.add_argument("--months", type=_positive_int)
    span.add_argument("--start", type=date.fromisoformat)
    ingest_cmd.add_argument("--end", type=date.fromisoformat)
    ingest_cmd.add_argument(
        "--refresh",
        action="store_true",
        help="Fetch from the API even if stored raw data exists",
    )
    return parser
