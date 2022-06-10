import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from caretaker.backend.abstract_backend import BackendFactory, AbstractBackend
from caretaker.utils import log
from caretaker.management.commands.create_backup import Command as CreateCommand
from caretaker.management.commands.push_backup import Command as PushCommand


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Creates a backup set and pushes it to the remote store"

    def add_arguments(self, parser):
        parser.add_argument('--output-directory')
        parser.add_argument('-a', '--additional-files',
                            action='append', required=False)

    def handle(self, *args, **options):
        """
        Creates a backup set and pushes it to the remote store

        :param args: the parser arguments
        :param options: the parser options
        :return: None
        """

        backend = BackendFactory.get_backend()

        if not backend:
            logger = log.get_logger('caretaker')
            logger.error('Unable to find a valid backend.')
            return

        self.run_backup(output_directory=options.get('output_directory'),
                        backend=backend,
                        bucket_name=settings.CARETAKER_BACKUP_BUCKET,
                        path_list=options.get('additional_files'))

    @staticmethod
    def run_backup(output_directory: str, data_file: str = 'data.json',
                   archive_file: str = 'media.zip',
                   path_list: list | None = None,
                   backend: AbstractBackend | None = None,
                   bucket_name: str | None = None) -> (Path | None,
                                                       Path | None):
        """
        Creates a backup set and pushes it to the remote store

        :param output_directory: the output directory for the local backup set
        :param data_file: the output data file (e.g. data.json)
        :param archive_file: the output archive file (e.g. media.zip)
        :param path_list: the list of paths to bundle in the zip
        :param backend: the backend to use
        :param bucket_name: the name of the bucket/store
        :return: 2-tuple of pathlib.Path objects to the data file & archive file
        """
        logger = log.get_logger('caretaker')

        if not path_list:
            path_list = []

        if not output_directory:
            logger.error('No output directory specified')
            return None, None

        # set up a temporary directory
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            # create a local backup set in this temporary directory
            create_command = CreateCommand()

            json_file, zip_file = create_command.create_backup(
                output_directory=temporary_directory_name,
                path_list=path_list
            )

            # push the data
            push_command = PushCommand()
            push_command.push_backup(backup_local_file=json_file,
                                     remote_key=data_file,
                                     backend=backend, bucket_name=bucket_name)
            push_command.push_backup(backup_local_file=zip_file,
                                     remote_key=archive_file,
                                     backend=backend, bucket_name=bucket_name)

            logger.info('Pushed backups to remote store')
            return json_file, archive_file
