from django.conf import settings
from django.core.management.base import BaseCommand

from caretaker.frontend.abstract_frontend import FrontendFactory
from caretaker.utils import log


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Pushes the backup to the remote store"

    def add_arguments(self, parser):
        parser.add_argument('--backup-local-file',
                            default='~/backup.sql')
        parser.add_argument('--remote-key',
                            default='backup.sql')

    def handle(self, *args, **options):
        """
        Pushes the backup to the remote store via a command

        :param args: the parser arguments
        :param options: the parser options
        :return: None
        """

        frontend, backend = FrontendFactory.get_frontend_and_backend()

        if not backend:
            logger = log.get_logger('caretaker')
            logger.error('Unable to find a valid backend.')
            return

        frontend.push_backup(backup_local_file=options.get('backup_local_file'),
                             remote_key=options.get('remote_key'),
                             backend=backend,
                             bucket_name=settings.CARETAKER_BACKUP_BUCKET)
