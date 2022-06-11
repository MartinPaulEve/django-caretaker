import importlib.resources as pkg_resources
from pathlib import Path
from typing import TextIO

from django.conf import settings
from django.template import Template, Context

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


def output_terraform_file(output_directory: Path, terraform_file: TextIO,
                          file_name: str) -> Path | None:
    """
    Writes a Terraform file to an output directory

    :param output_directory: the output directory
    :param terraform_file: the input file to template and copy
    :param file_name: the output filename
    :return: a pathlib.Path of the output file
    """

    with terraform_file as in_file:
        # render the terraform file into a template
        t = Template(in_file.read())
        c = Context({"bucket_name": settings.CARETAKER_BACKUP_BUCKET})
        rendered = t.render(c)

        # create the file structure
        output_directory.mkdir(parents=True, exist_ok=True)
        output_file = (output_directory / file_name)

        # write the terraform file to this directory
        with output_file.open('w') as out_file:
            out_file.write(rendered)

        return output_file
