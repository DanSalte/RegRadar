import json
from collections.abc import Callable
from datetime import date

import httpx
import pytest
from structlog.testing import capture_logs

from regradar.adapters.dip.dip_procedure_source import (
    API_BASE_URL,
    DipProcedureSource,
    DipRequestError,
    RetryPolicy,
    window_params,
)
from regradar.adapters.dip.rate_limit import RateLimiter
from regradar.core.application.errors import (
    AuthenticationError,
    InvalidDocumentError,
    SourceUnavailableError,
)
from regradar.core.domain.window import Window, WindowField
from tests.factories import raw_dip

WINDOW = Window(start=date(2026, 9, 1), end=date(2026, 9, 30))
TEST_CREDENTIAL = "test-value"

type Handler = Callable[[httpx.Request], httpx.Response]


def page(cursor: str, *ids: str) -> httpx.Response:
    documents = [raw_dip(source_id) for source_id in ids]
    body = {"numFound": len(ids), "cursor": cursor, "documents": documents}
    return httpx.Response(200, content=json.dumps(body))


class Recorder:
    """Answers requests from a script and records them."""

    def __init__(self, *responses: httpx.Response | Exception) -> None:
        self._responses = list(responses)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    @property
    def exhausted(self) -> bool:
        return not self._responses


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def make_source(
    handler: Handler,
    retry_sleeps: list[float] | None = None,
    clock: FakeClock | None = None,
) -> DipProcedureSource:
    clock = clock or FakeClock()
    sleeps = retry_sleeps if retry_sleeps is not None else []
    client = httpx.Client(
        base_url=API_BASE_URL, transport=httpx.MockTransport(handler)
    )
    return DipProcedureSource(
        client,
        TEST_CREDENTIAL,
        RateLimiter(1.0, clock=clock, sleep=clock.sleep),
        RetryPolicy(max_attempts=3, sleep=sleeps.append),
    )


def ids(source: DipProcedureSource) -> list[object]:
    return [document["id"] for document in source.fetch(WINDOW)]


def test_paginates_until_cursor_is_unchanged() -> None:
    recorder = Recorder(page("A", "1", "2"), page("B", "3"), page("B"))

    assert ids(make_source(recorder)) == ["1", "2", "3"]
    params = [request.url.params for request in recorder.requests]
    assert [p.get("cursor") for p in params] == [None, "A", "B"]
    assert all(p["f.datum.start"] == "2026-09-01" for p in params)
    assert all(p["f.datum.end"] == "2026-09-30" for p in params)
    assert all(p["apikey"] == TEST_CREDENTIAL for p in params)
    assert all(r.url.path == "/api/v1/vorgang" for r in recorder.requests)


def test_stops_when_unchanged_cursor_still_has_documents() -> None:
    recorder = Recorder(page("A", "1"), page("A", "1"))

    assert ids(make_source(recorder)) == ["1", "1"]
    assert recorder.exhausted


def test_stops_on_empty_first_page() -> None:
    recorder = Recorder(page("A"))

    assert ids(make_source(recorder)) == []
    assert len(recorder.requests) == 1


def test_retries_429_with_exponential_backoff() -> None:
    sleeps: list[float] = []
    recorder = Recorder(
        httpx.Response(429), httpx.Response(429), page("A", "1"), page("A")
    )

    with capture_logs() as logs:
        result = ids(make_source(recorder, sleeps))

    assert result == ["1"]
    assert sleeps == [1.0, 2.0]
    assert [e["status"] for e in logs if "status" in e] == [429, 429]


def test_retries_server_errors() -> None:
    sleeps: list[float] = []
    recorder = Recorder(httpx.Response(503), page("A", "1"), page("A"))

    assert ids(make_source(recorder, sleeps)) == ["1"]
    assert sleeps == [1.0]


def test_retries_network_errors() -> None:
    sleeps: list[float] = []
    recorder = Recorder(
        httpx.ConnectError("connection refused"), page("A", "1"), page("A")
    )

    with capture_logs() as logs:
        result = ids(make_source(recorder, sleeps))

    assert result == ["1"]
    assert sleeps == [1.0]
    error = next(e for e in logs if e["event"] == "dip_transport_error")
    assert error["exc_info"] is True


def test_gives_up_after_max_attempts() -> None:
    sleeps: list[float] = []
    recorder = Recorder(
        httpx.Response(500),
        httpx.ReadTimeout("timeout"),
        httpx.Response(502),
    )

    with pytest.raises(SourceUnavailableError, match="3 attempts"):
        ids(make_source(recorder, sleeps))

    assert recorder.exhausted
    assert sleeps == [1.0, 2.0]


@pytest.mark.parametrize("status", [401, 403])
def test_no_retry_on_rejected_api_key(status: int) -> None:
    sleeps: list[float] = []
    recorder = Recorder(httpx.Response(status))

    with pytest.raises(AuthenticationError, match=str(status)):
        ids(make_source(recorder, sleeps))

    assert len(recorder.requests) == 1
    assert sleeps == []


@pytest.mark.parametrize("status", [400, 404])
def test_no_retry_on_other_client_errors(status: int) -> None:
    sleeps: list[float] = []
    recorder = Recorder(httpx.Response(status, text="bad filter"))

    with pytest.raises(DipRequestError, match="bad filter"):
        ids(make_source(recorder, sleeps))

    assert len(recorder.requests) == 1
    assert sleeps == []


def test_unexpected_page_format_aborts() -> None:
    recorder = Recorder(httpx.Response(200, content=b'{"documents": 1}'))

    with pytest.raises(SourceUnavailableError, match="response format"):
        ids(make_source(recorder))


def test_requests_are_rate_limited() -> None:
    clock = FakeClock()
    recorder = Recorder(page("A", "1"), page("B", "2"), page("B"))

    ids(make_source(recorder, clock=clock))

    assert clock.sleeps == [1.0, 1.0]


def test_window_params_for_updated_field() -> None:
    window = Window(
        start=date(2026, 9, 1), end=date(2026, 9, 2), field=WindowField.UPDATED
    )

    assert window_params(window) == {
        "f.aktualisiert.start": "2026-09-01T00:00:00",
        "f.aktualisiert.end": "2026-09-02T23:59:59",
    }


def test_parse_maps_to_english_fields() -> None:
    source = make_source(Recorder())

    procedure = source.parse(raw_dip("338726"))

    assert procedure.source == "dip"
    assert procedure.source_id == "338726"
    assert procedure.title == "Gesetz zur Umsetzung der DORA-Verordnung"
    assert procedure.procedure_type == "Gesetzgebung"
    assert procedure.date == date(2026, 9, 1)
    assert procedure.status == "Beratung im Ausschuss"
    assert procedure.subject_areas == ("Wirtschaft",)
    assert [d.name for d in procedure.descriptors] == ["Kreditinstitut"]
    assert [d.kind for d in procedure.descriptors] == ["Sachbegriffe"]
    assert procedure.initiative == ("Bundesregierung",)
    assert procedure.source_url == (
        "https://dip.bundestag.de/vorgang/"
        "gesetz-zur-umsetzung-der-dora-verordnung/338726"
    )


def test_parse_accepts_missing_optional_fields() -> None:
    raw = raw_dip()
    for key in ("datum", "abstract", "sachgebiet", "deskriptor"):
        del raw[key]

    procedure = make_source(Recorder()).parse(raw)

    assert procedure.date is None
    assert procedure.abstract is None
    assert procedure.descriptors == ()


@pytest.mark.parametrize(
    "raw",
    [
        raw_dip(titel=None),
        raw_dip(id="abc"),
        raw_dip(aktualisiert="gestern"),
        {"id": "1"},
    ],
)
def test_parse_rejects_invalid_documents(raw: dict[str, object]) -> None:
    with pytest.raises(InvalidDocumentError):
        make_source(Recorder()).parse(raw)
