from pathlib import Path

import pytest

from regradar.core.application.errors import ConfigurationError
from regradar.core.domain.keyword_matcher import KeywordGroup
from regradar.entrypoints.keyword_config import load_keyword_groups

PROJECT_CONFIG = Path(__file__).parents[2] / "config" / "keywords.yaml"


def _write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "keywords.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_loads_groups_in_file_order(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """
groups:
  banks:
    label: Banken
    terms: [Kreditinstitut]
    acronyms: [KWG]
  cyber:
    label: Cyber
    terms: [Cyber]
    exclude: [Cybermobbing]
""",
    )

    groups = load_keyword_groups(path)

    assert groups == (
        KeywordGroup("banks", "Banken", ("Kreditinstitut",), ("KWG",)),
        KeywordGroup("cyber", "Cyber", ("Cyber",), (), ("Cybermobbing",)),
    )


def test_project_configuration_is_valid() -> None:
    assert load_keyword_groups(PROJECT_CONFIG)


@pytest.mark.parametrize(
    "content",
    [
        pytest.param("groups: {}", id="no groups"),
        pytest.param("groups:\n  a:\n    label: A", id="no terms"),
        pytest.param("groups:\n  a:\n    terms: [x]", id="no label"),
        pytest.param(
            "groups:\n  a:\n    label: A\n    terms: ['']", id="empty term"
        ),
        pytest.param(
            "groups:\n  a:\n    label: A\n    term: [x]", id="unknown key"
        ),
        pytest.param("groups: [", id="broken yaml"),
    ],
)
def test_rejects_invalid_configuration(tmp_path: Path, content: str) -> None:
    with pytest.raises(ConfigurationError, match="keyword configuration"):
        load_keyword_groups(_write(tmp_path, content))


def test_missing_file_is_a_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="keyword configuration"):
        load_keyword_groups(tmp_path / "missing.yaml")
