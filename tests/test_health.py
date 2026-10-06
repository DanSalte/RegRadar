import pytest

from regradar.core.domain.health import is_healthy


@pytest.mark.parametrize(("status", "expected"), [("ok", True), ("x", False)])
def test_is_healthy(status: str, expected: bool) -> None:
    assert is_healthy(status) is expected
