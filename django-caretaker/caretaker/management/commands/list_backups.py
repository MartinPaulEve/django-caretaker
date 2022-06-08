import humanize
from django.conf import settings
from django.core.management.base import BaseCommand

from caretaker.backend.abstract_backend import BackendFactory, AbstractBackend
from caretaker.utils import log


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Lists available backups"

    def add_arguments(self, parser):
        parser.add_argument('--remote-key',
                            default='backup.sql')

    def handle(self, *args, **options):
        """Lists available backups"""

        backend = BackendFactory.get_backend()

        if not backend:
            logger = log.get_logger('caretaker')
            logger.error('Unable to find a valid backend.')
            return

        self.list_backups(backend=backend,
                          remote_key=options.get('remote_key'),
                          bucket_name=settings.CARETAKER_BACKUP_BUCKET)

    @staticmethod
    def list_backups(remote_key: str, backend: AbstractBackend,
                     bucket_name: str) -> list[dict]:
        logger = log.get_logger('caretaker')

        results = backend.versions(remote_key=remote_key,
                                   bucket_name=bucket_name)

        for item in results:
            logger.info('Backup from {}: {} [{}]'.format(
                item['last_modified'],
                item['version_id'],
                humanize.naturalsize(item['size'])
            ))

        return results
