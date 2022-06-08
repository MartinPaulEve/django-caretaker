from pathlib import Path

from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand

import caretaker.utils.file as file
from caretaker.backend.abstract_backend import BackendFactory, AbstractBackend
from caretaker.utils import log


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Pulls a specific backup from the remote store"

    def add_arguments(self, parser):
        parser.add_argument('--backup-version')
        parser.add_argument('--out-file')
        parser.add_argument('--remote-key',
                            default='backup.sql')

    def handle(self, *args, **options):
        """
        Pulls a backup from S3
        """
        backend = BackendFactory.get_backend()

        if not backend:
            logger = log.get_logger('caretaker')
            logger.error('Unable to find a valid backend.')
            return

        self.pull_backup(out_file=options.get('backup_local_file'),
                         remote_key=options.get('remote_key'),
                         backend=backend,
                         bucket_name=settings.CARETAKER_BACKUP_BUCKET,
                         backup_version=options.get('backup_version'))

    @staticmethod
    def pull_backup(backup_version: str, out_file: str, remote_key: str,
                    backend: AbstractBackend, bucket_name: str) -> Path | None:
        logger = log.get_logger('caretaker')

        out_file = file.normalize_path(out_file)

        download = backend.download_object(local_file=out_file,
                                           remote_key=remote_key,
                                           version_id=backup_version,
                                           bucket_name=bucket_name)

        try:
            if download:

                return out_file
            else:
                raise ClientError
        except ClientError:
            logger.error('Unable to download version {} of {} to {}'.format(
                backup_version,
                remote_key,
                out_file
            ))

            return None
