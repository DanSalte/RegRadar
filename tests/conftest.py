import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import quote, unquote

import pytest
import structlog

CASSETTES = Path(__file__).parent / "cassettes"
_CURSOR_PREFIX = "recorded-cursor-"
_URI_CURSOR = re.compile(r"(?<=[?&]cursor=)[^&]*")
_BODY_CURSOR = re.compile(r'(?<="cursor":")[^"]*')


class _VcrRequest(Protocol):
    uri: str


class CursorMask:
    """Replaces DIP's opaque paging cursors in cassettes.

    The cursors are high-entropy strings that the secret scan flags
    (ADR-0006 demands no findings). They are mapped consistently, so
    replayed responses lead to exactly the recorded follow-up requests.
    """

    def __init__(self) -> None:
        self._masks: dict[str, str] = {}

    def mask(self, cursor: str) -> str:
        if cursor.startswith(_CURSOR_PREFIX):
            return cursor
        default = f"{_CURSOR_PREFIX}{len(self._masks) + 1}"
        return self._masks.setdefault(cursor, default)

    def request(self, request: _VcrRequest) -> _VcrRequest:
        request.uri = _URI_CURSOR.sub(
            lambda m: quote(self.mask(unquote(m.group()))), request.uri
        )
        return request

    def response(self, response: dict[str, Any]) -> dict[str, Any]:
        body = response["body"]["string"]
        text = body.decode() if isinstance(body, bytes) else body
        masked = _BODY_CURSOR.sub(lambda m: self.mask(m.group()), text)
        response["body"]["string"] = masked.encode()
        return response


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, object]:
    cursors = CursorMask()
    return {
        "filter_query_parameters": ["apikey"],
        "decode_compressed_response": True,
        "before_record_request": cursors.request,
        "before_record_response": cursors.response,
    }


@pytest.fixture
def vcr_cassette_dir(request: pytest.FixtureRequest) -> str:
    return str(CASSETTES / request.path.stem)


@pytest.fixture(autouse=True)
def _reset_structlog() -> Iterator[None]:
    # The CLI configures structlog globally; keep tests independent.
    yield
    structlog.reset_defaults()
