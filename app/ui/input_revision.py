"""Cheap local file revision checks for preview gates (not remote freshness)."""
from pathlib import Path


def file_revision(value: str | Path) -> tuple:
    path = Path(value)
    try:
        stat = path.stat()
        return (str(path.resolve()), stat.st_size, stat.st_mtime_ns, stat.st_ino)
    except OSError:
        return (str(path), None)
