from pathlib import Path


def normalize_path(path: str) -> Path:
    return Path(path).expanduser()
