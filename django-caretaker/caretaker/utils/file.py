from pathlib import Path
import importlib.resources as pkg_resources
from typing import TextIO

from caretaker.backend.abstract_backend import AbstractBackend


def normalize_path(path: str | Path) -> Path:
    """
    Normalize paths by a standard method

    :param path: the location on disk
    :return: a pathlib.Path object
    """
    return Path(path).expanduser()


def get_package_file(filename: str, backend: AbstractBackend) -> TextIO:

    return pkg_resources.open_text(backend.terraform_template_module,
                                   filename)
