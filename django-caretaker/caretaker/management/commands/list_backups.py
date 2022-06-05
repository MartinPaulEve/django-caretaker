import boto3
import humanize
from django.conf import settings
from django.core.management.base import BaseCommand
from caretaker.main_utils import log


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

        s3 = boto3.client('s3',
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

        self._list_backups(s3_client=s3, remote_key=options.get('remote_key'),
                           bucket_name=settings.BACKUP_BUCKET)

    @staticmethod
    def _list_backups(remote_key, s3_client, bucket_name):
        logger = log.get_logger('caretaker')

        s3 = s3_client

        versions = s3.list_object_versions(Bucket=bucket_name,
                                           Prefix=remote_key)

        if versions and 'Versions' in versions:
            for item in versions['Versions']:
                logger.info('Backup from {}: {} [{}]'.format(
                    item['LastModified'],
                    item['VersionId'],
                    humanize.naturalsize(item['Size'])
                ))

            return versions['Versions']

        return None
