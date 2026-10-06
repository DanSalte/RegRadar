import json
from datetime import date
from pathlib import Path

import httpx
import pytest
from structlog.testing import capture_logs

from regradar.core.application.errors import ConfigurationError, SystemicError
from regradar.core.application.ingest import RunSummary
from regradar.core.domain.window import Window
from regradar.entrypoints import cli
from tests.factories import raw_dip

WINDOW = Window(start=date(2026, 9, 1), end=date(2026, 9, 30))


@pytest.fixture
def paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> cli.Paths:
    # Run in an empty directory so that no real .env is picked up.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DIP_API_KEY", "test-key")
    return cli.Paths(
        raw_dir=tmp_path / "data" / "raw",
        dead_letters=tmp_path / "data" / "raw" / "dead_letters.jsonl",
    )


class FakeDip:
    def __init__(self, *documents: dict[str, object]) -> None:
        self.documents = list(documents)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        cursor = request.url.params.get("cursor")
        body = {
            "numFound": len(self.documents),
            "cursor": "end",
            "documents": [] if cursor else self.documents,
        }
        return httpx.Response(200, content=json.dumps(body))


def run(
    paths: cli.Paths, dip: FakeDip, *, refresh: bool = False
) -> tuple[int, list[float]]:
    sleeps: list[float] = []
    code = cli.ingest_dip(
        WINDOW,
        refresh=refresh,
        paths=paths,
        transport=httpx.MockTransport(dip),
        sleep=sleeps.append,
    )
    return code, sleeps


def stored_ids(paths: cli.Paths) -> list[str]:
    [path] = paths.raw_dir.glob("dip_procedure_*.jsonl")
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line)["id"] for line in lines]


def test_fetches_and_stores_raw_data(paths: cli.Paths) -> None:
    dip = FakeDip(raw_dip("1"), raw_dip("2", titel="Haushaltsgesetz"))

    code, sleeps = run(paths, dip)

    assert code == cli.EXIT_OK
    assert len(dip.requests) == len(sleeps) + 1
    assert stored_ids(paths) == ["1", "2"]


def test_second_run_without_refresh_makes_no_api_calls(
    paths: cli.Paths,
) -> None:
    run(paths, FakeDip(raw_dip("1")))
    second = FakeDip(raw_dip("2"))

    with capture_logs() as logs:
        code, _ = run(paths, second)

    assert code == cli.EXIT_OK
    assert second.requests == []
    assert stored_ids(paths) == ["1"]
    assert "raw_data_reused" in [e["event"] for e in logs]


def test_refresh_calls_api_again(paths: cli.Paths) -> None:
    run(paths, FakeDip(raw_dip("1")))
    second = FakeDip(raw_dip("2"), raw_dip("3"))

    run(paths, second, refresh=True)

    assert second.requests
    assert stored_ids(paths) == ["2", "3"]


def test_invalid_document_goes_to_dead_letters(paths: cli.Paths) -> None:
    valid = [raw_dip(str(i)) for i in range(1, 40)]

    code, _ = run(paths, FakeDip(*valid, raw_dip("40", titel=None)))

    assert code == cli.EXIT_OK
    lines = paths.dead_letters.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["document"]["id"] for line in lines] == ["40"]


def test_high_failure_rate_fails_the_run(paths: cli.Paths) -> None:
    dip = FakeDip(raw_dip("1"), raw_dip("2", titel=None))

    code, _ = run(paths, dip)

    assert code == cli.EXIT_RUN_FAILED


def test_missing_api_key_is_systemic(
    paths: cli.Paths, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("DIP_API_KEY")

    with pytest.raises(ConfigurationError, match="DIP_API_KEY"):
        run(paths, FakeDip())


def test_finish_detects_unreconciled_run() -> None:
    summary = RunSummary(loaded=3, stored=1, discarded=0, failed=0)

    with capture_logs() as logs:
        code = cli._finish(summary)

    assert code == cli.EXIT_RUN_FAILED
    assert "run_does_not_reconcile" in [e["event"] for e in logs]


def test_finish_warns_below_threshold() -> None:
    summary = RunSummary(loaded=100, stored=99, discarded=0, failed=1)

    with capture_logs() as logs:
        code = cli._finish(summary)

    assert code == cli.EXIT_OK
    assert "documents_failed" in [e["event"] for e in logs]


def test_main_passes_window_to_run(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[Window, bool]] = []

    def fake(window: Window, *, refresh: bool, paths: cli.Paths) -> int:
        calls.append((window, refresh))
        return cli.EXIT_OK

    monkeypatch.setattr(cli, "ingest_dip", fake)

    code = cli.main(
        ["ingest-dip", "--start", "2026-09-01", "--end", "2026-09-30"]
    )

    assert code == cli.EXIT_OK
    assert calls == [(WINDOW, False)]


def test_main_months_and_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[Window, bool]] = []

    def fake(window: Window, *, refresh: bool, paths: cli.Paths) -> int:
        calls.append((window, refresh))
        return cli.EXIT_OK

    monkeypatch.setattr(cli, "ingest_dip", fake)

    cli.main(["ingest-dip", "--months", "1", "--refresh"])

    [(window, refresh)] = calls
    assert refresh is True
    assert window == Window.last_months(date.today(), 1)


def test_main_aborts_on_systemic_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake(window: Window, *, refresh: bool, paths: cli.Paths) -> int:
        msg = "DIP down"
        raise SystemicError(msg)

    monkeypatch.setattr(cli, "ingest_dip", fake)

    code = cli.main(["ingest-dip", "--months", "1"])

    assert code == cli.EXIT_ABORTED
    event = json.loads(capsys.readouterr().err.splitlines()[-1])
    assert event["event"] == "run_aborted"
    assert event["exception"][0]["exc_value"] == "DIP down"


@pytest.mark.parametrize(
    "argv",
    [
        ["ingest-dip"],
        ["ingest-dip", "--months", "0"],
        ["ingest-dip", "--months", "x"],
        ["ingest-dip", "--months", "1", "--start", "2026-09-01"],
        ["ingest-dip", "--months", "1", "--end", "2026-09-01"],
        ["ingest-dip", "--start", "2026-09-01"],
        ["ingest-dip", "--start", "2026-09-02", "--end", "2026-09-01"],
    ],
)
def test_invalid_arguments(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        cli.main(argv)

    assert exit_info.value.code == cli.EXIT_ABORTED
