from pathlib import Path


def normalize_path(path: str | Path) -> Path:
    """
    Normalize paths by a standard method
    :param path: the location on disk
    :return: a pathlib.Path object
    """
    return Path(path).expanduser()
