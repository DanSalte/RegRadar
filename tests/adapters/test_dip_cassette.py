import os
from datetime import date

import httpx
import pytest

from regradar.adapters.dip.dip_procedure_source import (
    API_BASE_URL,
    DipProcedureSource,
    RetryPolicy,
)
from regradar.adapters.dip.rate_limit import RateLimiter
from regradar.core.domain.window import Window

# Recording needs a real key (`DIP_API_KEY=... pytest --record-mode=once`);
# the cassette stores it filtered, so replay works with any value.
API_KEY = os.environ.get("DIP_API_KEY", "replay")


@pytest.mark.vcr
def test_fetches_and_parses_real_response() -> None:
    window = Window(start=date(2026, 9, 1), end=date(2026, 9, 1))
    with httpx.Client(base_url=API_BASE_URL) as client:
        source = DipProcedureSource(
            client, API_KEY, RateLimiter(1.0), RetryPolicy(max_attempts=1)
        )
        documents = list(source.fetch(window))

    procedures = [source.parse(document) for document in documents]

    assert procedures
    assert len({p.source_id for p in procedures}) == len(procedures)
    assert all(p.title and p.procedure_type for p in procedures)
    assert any(p.descriptors for p in procedures)
