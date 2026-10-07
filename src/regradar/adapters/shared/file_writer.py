"""Building block (shared by adapters): atomic file writes."""

import os
import tempfile
from pathlib import Path


def write_file_atomically(path: Path, content: str) -> None:
    """Readers see the old or the new file, never a partial one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
