from pathlib import Path

import pytest

from regradar.adapters.shared.file_writer import write_file_atomically


def test_write_file_atomically_creates_parents_and_replaces(
    tmp_path: Path,
) -> None:
    path = tmp_path / "a" / "b.txt"

    write_file_atomically(path, "first")
    write_file_atomically(path, "zweite Ä")

    assert path.read_text(encoding="utf-8") == "zweite Ä"
    assert list(path.parent.iterdir()) == [path]


def test_write_file_atomically_keeps_old_file_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "b.txt"
    path.write_text("old", encoding="utf-8")

    def fail(self: Path, target: Path) -> Path:
        msg = "disk full"
        raise OSError(msg)

    monkeypatch.setattr(Path, "replace", fail)

    with pytest.raises(OSError, match="disk full"):
        write_file_atomically(path, "new")

    assert path.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.iterdir()) == [path]
