import tempfile

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from caretaker.management.commands.create_backup import Command as CreateCommand
from caretaker.management.commands.push_backup import Command as PushCommand

from caretaker.main_utils import log


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Creates a backup set and pushes it to S3"

    def add_arguments(self, parser):
        parser.add_argument('--output-directory')

    def handle(self, *args, **options):
        """
        Creates a backup set and pushes it to S3
        """
        s3 = boto3.client('s3',
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

        self._run_backup(options.get('output_directory'), s3_client=s3,
                         bucket_name=settings.BACKUP_BUCKET)

    @staticmethod
    def _run_backup(output_directory, data_file='data.json',
                    archive_file='media.zip', path_list=None,
                    s3_client=None, bucket_name=None):
        logger = log.get_logger('caretaker')

        s3 = s3_client

        if not path_list:
            path_list = []

        if not output_directory:
            logger.error('No output directory specified')
            return None, None

        # set up a temporary directory
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            # create a local backup set in this temporary directory
            create_command = CreateCommand()

            json_file, zip_file = create_command._create_backup(
                output_directory=temporary_directory_name,
                path_list=path_list
            )

            # push the data
            push_command = PushCommand()
            push_command._push_backup(backup_local_file=json_file,
                                      remote_key=data_file,
                                      s3_client=s3, bucket_name=bucket_name)
            push_command._push_backup(backup_local_file=zip_file,
                                      remote_key=archive_file,
                                      s3_client=s3, bucket_name=bucket_name)

            logger.info('Pushed backups to remote store')
            return json_file, archive_file
