from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from caretaker.backend.abstract_backend import BackendFactory, StoreOutcome
from caretaker.main_utils import log


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
        Pushes the backup to S3
        """

        backend = BackendFactory.get_backend()

        if not backend:
            logger = log.get_logger('caretaker')
            logger.error('Unable to find a valid backend.')
            return

        self.push_backup(backup_local_file=options.get('backup_local_file'),
                         remote_key=options.get('remote_key'),
                         backend=backend,
                         bucket_name=settings.CARETAKER_BACKUP_BUCKET)

    @staticmethod
    def push_backup(backup_local_file, remote_key, backend,
                    bucket_name):

        logger = log.get_logger('caretaker')

        backup_local_file = Path(backup_local_file).expanduser()

        result = backend.store_object(remote_key=remote_key,
                                      bucket_name=bucket_name,
                                      local_file=backup_local_file,
                                      check_identical=True)

        match result:
            case StoreOutcome.STORED:
                logger.info('Stored backup.')
            case StoreOutcome.FAILED:
                logger.info('Failed to store backup.')
            case StoreOutcome.IDENTICAL:
                logger.info('Last version was identical.')

        return result
