from django.conf import settings
from django.core.management.base import BaseCommand

from caretaker.utils import log
from caretaker.frontend.abstract_frontend import FrontendFactory


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Lists available backups"

    def add_arguments(self, parser):
        parser.add_argument('--remote-key',
                            default='backup.sql')

    def handle(self, *args, **options):
        """
        Lists backups in the remote store via a command

        :param args: the parser arguments
        :param options: the parser options
        :return: None
        """

        frontend, backend = FrontendFactory.get_frontend_and_backend()

        if not backend:
            logger = log.get_logger('caretaker')
            logger.error('Unable to find a valid backend.')
            return

        frontend.list_backups(backend=backend,
                              remote_key=options.get('remote_key'),
                              bucket_name=settings.CARETAKER_BACKUP_BUCKET)
