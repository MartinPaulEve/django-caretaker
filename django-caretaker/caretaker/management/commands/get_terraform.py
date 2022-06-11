from django.core.management.base import BaseCommand

from caretaker.utils import log
from caretaker.frontend.abstract_frontend import FrontendFactory


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Gets a terraform setup configuration"

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
        frontend, backend = FrontendFactory.get_frontend_and_backend()

        if not backend:
            logger = log.get_logger('caretaker')
            logger.error('Unable to find a valid backend.')
            return

        frontend.generate_terraform(
            output_directory=options.get('output_directory'),
            backend=backend
        )
