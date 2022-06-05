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

    help = "Pulls a specific backup from the S3 store"

    def add_arguments(self, parser):
        parser.add_argument('--backup-version')
        parser.add_argument('--out-file')
        parser.add_argument('--remote-key',
                            default='backup.sql')

    def handle(self, *args, **options):
        """
        Pulls a backup from S3
        """
        s3 = boto3.client('s3',
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

        self._pull_backup(out_file=options.get('backup_local_file'),
                          remote_key=options.get('remote_key'),
                          s3_client=s3, bucket_name=settings.BACKUP_BUCKET,
                          backup_version=options.get('backup_version'))

    @staticmethod
    def _pull_backup(backup_version, out_file, remote_key, s3_client,
                     bucket_name):
        logger = log.get_logger('caretaker')

        s3 = s3_client

        out_file = Path(out_file).expanduser()

        try:
            s3.download_file(
                Filename=str(out_file),
                Bucket=bucket_name,
                Key=remote_key,
                ExtraArgs={'VersionId': backup_version}
            )

            logger.info('Saved version {} of {} to {}'.format(
                backup_version,
                remote_key,
                out_file
            ))

            return out_file
        except ClientError:
            logger.error('Unable to download version {} of {} to {}'.format(
                backup_version,
                remote_key,
                out_file
            ))
            return None
