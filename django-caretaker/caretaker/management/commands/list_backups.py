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
        """
        Lists backups in the remote store via a command

        :param args: the parser arguments
        :param options: the parser options
        :return: None
        """

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
        """
        Lists backups in the remote store

        :param remote_key: the remote key (filename)
        :param backend: the backend to use
        :param bucket_name: the name of the bucket/store
        :return: a list of dictionaries that contain the keys "last_modified", "version_id", and "size"
        """
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
