from django.conf import settings
from django.core.management.base import BaseCommand

from caretaker.utils import log
from caretaker.frontend.abstract_frontend import FrontendFactory


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Creates a backup set and pushes it to the remote store"

    def add_arguments(self, parser):
        parser.add_argument('--output-directory')
        parser.add_argument('-a', '--additional-files',
                            action='append', required=False)

    def handle(self, *args, **options):
        """
        Creates a backup set and pushes it to the remote store

        :param args: the parser arguments
        :param options: the parser options
        :return: None
        """

        frontend, backend = FrontendFactory.get_frontend_and_backend()

        if not backend:
            logger = log.get_logger('caretaker')
            logger.error('Unable to find a valid backend.')
            return

        frontend.run_backup(output_directory=options.get('output_directory'),
                            backend=backend,
                            bucket_name=settings.CARETAKER_BACKUP_BUCKET,
                            path_list=options.get('additional_files'))
