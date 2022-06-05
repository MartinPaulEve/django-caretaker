import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import Template, Context

from caretaker.main_utils import log


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Gets a terraform setup configuration"

    @staticmethod
    def _output_terraform_file(output_directory, terraform_file, file_name):
        with terraform_file.open('r') as in_file:
            # render the terraform file into a template
            t = Template(in_file.read())
            c = Context({"bucket_name": settings.BACKUP_BUCKET})
            rendered = t.render(c)

            # create the file structure
            output_directory.mkdir(parents=True, exist_ok=True)

            # write the terraform file to this directory
            with (output_directory / file_name).open('w') as out_file:
                out_file.write(rendered)

    @staticmethod
    def _generate_terraform(output_directory):
        logger = log.get_logger('caretaker')
        output_directory = Path(output_directory).expanduser()

        # configure file paths
        terraform_dir = Path(
            os.path.realpath(__file__)).parent.parent.parent / 'terraform'

        terraform_file = Path(terraform_dir / 'main.tf')
        terraform_output_file = Path(terraform_dir / 'output.tf')

        Command._output_terraform_file(
            output_directory, terraform_file, 'main.tf')
        Command._output_terraform_file(
            output_directory, terraform_output_file, 'output.tf')

        logger.info('Terraform files were written to {}'.format(
            output_directory))

    def add_arguments(self, parser):
        parser.add_argument('--output-directory',
                            default='~/terraform_configuration')

    def handle(self, *args, **options):
        """
        Produces a Terraform setup configuration
        """
        self._generate_terraform(options.get('output_directory'))
