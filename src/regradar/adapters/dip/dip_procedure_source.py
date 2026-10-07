import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Final

import httpx
import pydantic
import structlog

from regradar.adapters.dip.api_dto import DipPageDto, DipProcedureDto
from regradar.adapters.dip.rate_limit import RateLimiter
from regradar.adapters.dip.web_url import procedure_web_url
from regradar.core.application.errors import (
    AuthenticationError,
    InvalidDocumentError,
    SourceUnavailableError,
    SystemicError,
)
from regradar.core.application.ports.raw_document import RawDocument
from regradar.core.domain.procedure import Descriptor, Procedure
from regradar.core.domain.window import Window, WindowField

log = structlog.get_logger()

API_BASE_URL: Final = "https://search.dip.bundestag.de/api/v1"
SOURCE: Final = "dip"
_AUTH_ERRORS: Final = frozenset({401, 403})
_TOO_MANY_REQUESTS: Final = 429
_SERVER_ERROR: Final = 500
_CLIENT_ERROR: Final = 400


class DipRequestError(SystemicError):
    """The API rejected the request itself; retrying will not help."""


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 5
    backoff_seconds: float = 1.0
    sleep: Callable[[float], None] = field(default=time.sleep)

    def delay(self, attempt: int) -> float:
        return self.backoff_seconds * 2.0 ** (attempt - 1)


class DipProcedureSource:
    def __init__(
        self,
        client: httpx.Client,
        api_key: str,
        rate_limiter: RateLimiter,
        retry: RetryPolicy,
    ) -> None:
        self._client = client
        self._api_key = api_key
        self._rate_limiter = rate_limiter
        self._retry = retry

    def fetch(self, window: Window) -> Iterator[RawDocument]:
        params = window_params(window)
        cursor: str | None = None
        while True:
            page = self._get_page(params, cursor)
            yield from page.documents
            # DIP signals the last page by returning the cursor unchanged.
            if not page.documents or page.cursor == cursor:
                return
            cursor = page.cursor

    def parse(self, raw: RawDocument) -> Procedure:
        try:
            model = DipProcedureDto.model_validate(raw)
        except pydantic.ValidationError as err:
            raise InvalidDocumentError(str(err)) from err
        return to_procedure(model)

    def _get_page(
        self, params: dict[str, str], cursor: str | None
    ) -> DipPageDto:
        query = {**params, "apikey": self._api_key}
        if cursor is not None:
            query["cursor"] = cursor
        response = self._request(query)
        try:
            return DipPageDto.model_validate_json(response.content)
        except pydantic.ValidationError as err:
            msg = "DIP returned an unexpected response format"
            raise SourceUnavailableError(msg) from err

    def _request(self, query: dict[str, str]) -> httpx.Response:
        for attempt in range(1, self._retry.max_attempts + 1):
            response = self._attempt(query, attempt)
            if response is not None:
                return response
            if attempt < self._retry.max_attempts:
                self._retry.sleep(self._retry.delay(attempt))
        msg = f"DIP unreachable after {self._retry.max_attempts} attempts"
        raise SourceUnavailableError(msg)

    def _attempt(
        self, query: dict[str, str], attempt: int
    ) -> httpx.Response | None:
        """Returns None if the request should be retried."""
        self._rate_limiter.wait()
        try:
            response = self._client.get("/vorgang", params=query)
        except httpx.TransportError:
            log.exception("dip_transport_error", attempt=attempt)
            return None
        status = response.status_code
        if status in _AUTH_ERRORS:
            msg = f"DIP rejected the API key (HTTP {status})"
            raise AuthenticationError(msg)
        if status == _TOO_MANY_REQUESTS or status >= _SERVER_ERROR:
            log.warning("dip_retryable_status", status=status, attempt=attempt)
            return None
        if status >= _CLIENT_ERROR:
            msg = f"DIP rejected the request (HTTP {status}): {response.text}"
            raise DipRequestError(msg)
        return response


def window_params(window: Window) -> dict[str, str]:
    if window.field is WindowField.DATE:
        return {
            "f.datum.start": window.start.isoformat(),
            "f.datum.end": window.end.isoformat(),
        }
    return {
        "f.aktualisiert.start": f"{window.start.isoformat()}T00:00:00",
        "f.aktualisiert.end": f"{window.end.isoformat()}T23:59:59",
    }


def to_procedure(model: DipProcedureDto) -> Procedure:
    return Procedure(
        source=SOURCE,
        source_id=model.id,
        source_url=procedure_web_url(model.title, model.id),
        title=model.title,
        procedure_type=model.procedure_type,
        updated=model.updated,
        date=model.date,
        abstract=model.abstract,
        status=model.status,
        subject_areas=tuple(model.subject_areas),
        descriptors=tuple(
            Descriptor(name=d.name, kind=d.kind) for d in model.descriptors
        ),
        initiative=tuple(model.initiative),
    )
