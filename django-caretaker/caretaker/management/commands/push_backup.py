import filecmp
import tempfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand

from caretaker.main_utils import log


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Pushes the backup to the S3 store"

    returns = {0: 'FAILED',
               1: 'STORED',
               2: 'IDENTICAL'}

    def add_arguments(self, parser):
        parser.add_argument('--backup-local-file',
                            default='~/backup.sql')
        parser.add_argument('--remote-key',
                            default='backup.sql')

    def handle(self, *args, **options):
        """
        Pushes the backup to S3
        """
        s3 = boto3.client('s3',
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

        self._push_backup(backup_local_file=options.get('backup_local_file'),
                          remote_key=options.get('remote_key'),
                          s3_client=s3, bucket_name=settings.BACKUP_BUCKET)

    def _push_backup(self, backup_local_file, remote_key, s3_client,
                     bucket_name):
        logger = log.get_logger('caretaker')

        backup_local_file = Path(backup_local_file).expanduser()

        s3 = s3_client

        # download the latest version of the backup to see if it's the same
        # as the local file
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'latest'

                s3.download_file(Filename=str(path), Bucket=bucket_name,
                                 Key=remote_key)

                if filecmp.cmp(path, backup_local_file):
                    logger.info('Latest backup is equal to remote S3 version')
                    return self.returns[2]

        except ClientError:
            logger.error('There was a problem comparing the previous version '
                         'of this log with the stored version. This is not '
                         'a fatal error.')
            pass

        try:
            # upload the latest version to S3
            s3.upload_file(Filename=str(backup_local_file),
                           Bucket=bucket_name, Key=remote_key)

            logger.info('Backup {} stored as {}'.format(
                backup_local_file, remote_key))
        except ClientError:
            logger.error('There was a problem storing the backup.')
            return self.returns[0]

        return self.returns[1]
