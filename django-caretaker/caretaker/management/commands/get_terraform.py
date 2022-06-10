from pathlib import Path
from typing import BinaryIO

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import Template, Context

from caretaker.backend.abstract_backend import AbstractBackend, BackendFactory
from caretaker.utils import log, file


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Gets a terraform setup configuration"

    @staticmethod
    def _output_terraform_file(output_directory: Path, terraform_file: BinaryIO,
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

    @staticmethod
    def generate_terraform(output_directory: str,
                           backend: AbstractBackend) -> Path | None:
        """
        Generate a set of Terraform output files to provision an infrastructure

        :param output_directory: the output directory to write to
        :param backend: the backend to use
        :return: a path indicating where the Terraform files reside
        """
        logger = log.get_logger('caretaker')
        output_directory = file.normalize_path(output_directory)

        # configure file paths
        terraform_file = file.get_package_file(backend=backend,
                                               filename='main.tf')

        terraform_output_file = file.get_package_file(backend=backend,
                                                      filename='output.tf')

        Command._output_terraform_file(
            output_directory, terraform_file, 'main.tf')
        Command._output_terraform_file(
            output_directory, terraform_output_file, 'output.tf')

        logger.info('Terraform files were written to {}'.format(
            output_directory))

        return output_directory

    def add_arguments(self, parser):
        parser.add_argument('--output-directory',
                            default='~/terraform_configuration')

    def handle(self, *args, **options):
        """
        Produces a Terraform setup configuration via a command

        :param args: the parser arguments
        :param options: the parser options
        :return: None
        """
        backend = BackendFactory.get_backend()

        if not backend:
            logger = log.get_logger('caretaker')
            logger.error('Unable to find a valid backend.')
            return

        self.generate_terraform(
            output_directory=options.get('output_directory'),
            backend=backend
        )
