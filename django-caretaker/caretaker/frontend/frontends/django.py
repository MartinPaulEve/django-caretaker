import io
import logging
import tempfile
from io import StringIO
from pathlib import Path
import subprocess

from django.db import DEFAULT_DB_ALIAS, connections

from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management import call_command

from caretaker.backend.abstract_backend import AbstractBackend, StoreOutcome
from caretaker.frontend.abstract_frontend import AbstractFrontend, FrontendError
from caretaker.utils import log, file
from caretaker.utils.zip import create_zip_file

from django.core.management.base import BaseCommand, CommandError
import caretaker.frontend.frontends.utils as frontend_utils

def get_frontend():
    return DjangoFrontend()


class DjangoFrontend(AbstractFrontend):
    @staticmethod
    def export_sql(database: str = '') -> str:

        database = database if database else DEFAULT_DB_ALIAS
        connection = connections[database]

        # load the database patch plugins
        frontend_utils.PluginLoader.patch(connection)

        print(connection.__dict__)

        try:
            pass
        except FileNotFoundError:
            # Note that we're assuming the FileNotFoundError relates to the
            # command missing. It could be raised for some other reason, in
            # which case this error message would be inaccurate. Still, this
            # message catches the common case.
            raise CommandError(
                "You appear not to have the %r program installed or on "
                "your path."
                % connection.client.executable_name
            )
        except subprocess.CalledProcessError as e:
            raise CommandError(
                '"%s" returned non-zero exit status %s.'
                % (
                    " ".join(e.cmd),
                    e.returncode,
                ),
                returncode=e.returncode,
            )

    @staticmethod
    def pull_backup_bytes(backup_version: str, remote_key: str,
                          backend: AbstractBackend,
                          bucket_name: str,
                          raise_on_error: bool = False) -> io.BytesIO | None:
        """
        Pull a backup object from the remote store into a BytesIO object

        :param backup_version: the version ID of the backup to pull
        :param remote_key: the remote key (filename)
        :param backend: the backend to use
        :param bucket_name: the name of the bucket/store
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: a pathlib.Path object pointing to the downloaded file or None
        """
        return backend.get_object(
            bucket_name=bucket_name,
            remote_key=remote_key, version_id=backup_version,
            raise_on_error=raise_on_error
        )

    def __init__(self, logger: logging.Logger | None = None):
        super().__init__(logger)

        self.logger = log.get_logger('caretaker-django')

    @property
    def frontend_name(self) -> str:
        """
        The display name of the frontend

        :return: a string of the frontend name
        """
        return 'Django'

    @staticmethod
    def create_backup(output_directory: str, data_file: str = 'data.json',
                      archive_file: str = 'media.zip',
                      path_list: list | None = None,
                      raise_on_error: bool = False) -> (Path | None,
                                                        Path | None):
        """
        Creates a set of local backup files

        :param output_directory: the output location
        :param data_file: the output data file (e.g. data.json)
        :param archive_file: the output archive file (e.g. media.zip)
        :param path_list: the list of paths to bundle in the zip
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: a 2-tuple of pathlib.Path objects to the data file and archive file
        """
        logger = log.get_logger('caretaker-django')

        if not output_directory:
            logger.error('No output directory specified')

            if raise_on_error:
                raise FileNotFoundError

            return None, None

        # create the directory if needed
        output_directory = Path(output_directory)

        output_directory.mkdir(parents=True, exist_ok=True)

        output_directory = file.normalize_path(output_directory)

        # setup redirect so that we can pipe the output of dump data to
        # our output file
        buffer = StringIO()
        call_command('dumpdata', stdout=buffer)
        buffer.seek(0)

        with (output_directory / data_file).open('w') as out_file:
            out_file.write(buffer.read())
            logger.info('Wrote {}'.format(data_file))

        # now create a zip of the media directory and any others specified
        path_list = [] if not path_list else path_list
        path_list = list(set(path_list))

        if hasattr(settings, 'MEDIA_ROOT') and \
                settings.MEDIA_ROOT and settings.MEDIA_ROOT not in path_list:
            logger.info('Appending MEDIA_ROOT')
            path_list.append(settings.MEDIA_ROOT)

        if hasattr(settings, 'CARETAKER_ADDITIONAL_BACKUP_PATHS') \
                and settings.CARETAKER_ADDITIONAL_BACKUP_PATHS \
                and settings.CARETAKER_ADDITIONAL_BACKUP_PATHS not in path_list:
            logger.info('Appending CARETAKER_ADDITIONAL_BACKUP_PATHS')
            path_list.extend(settings.CARETAKER_ADDITIONAL_BACKUP_PATHS)

        path_list_final = []

        for path in path_list:
            path = file.normalize_path(path)

            path_list_final.append(file.normalize_path(path))

            if not path.exists():
                logger.error('Could not find {}'.format(path))
                raise FileNotFoundError()

        logger.info('Paths to be zipped: '.format(path_list_final))

        zip_file = create_zip_file(
            input_paths=list(path_list_final),
            output_file=Path(output_directory / archive_file)
        )

        logger.info('Wrote {} ({})'.format(archive_file, zip_file))

        return output_directory / data_file, zip_file

    @staticmethod
    def generate_terraform(output_directory: str,
                           backend: AbstractBackend) -> Path | None:
        """
        Generate a set of Terraform output files to provision an infrastructure

        :param output_directory: the output directory to write to
        :param backend: the backend to use
        :return: a path indicating where the Terraform files reside
        """
        logger = log.get_logger('caretaker')
        output_directory = file.normalize_path(output_directory)

        for filename in backend.terraform_files:
            terraform_file = file.get_package_file(backend=backend,
                                                   filename=filename)
            logger.info('Writing {} to {}'.format(filename, output_directory))
            file.output_terraform_file(
                output_directory=output_directory,
                terraform_file=terraform_file, file_name=filename)

        logger.info('Terraform files were written to {}'.format(
            output_directory))

        return output_directory

    @staticmethod
    def list_backups(remote_key: str, backend: AbstractBackend,
                     bucket_name: str, raise_on_error: bool = False) \
            -> list[dict]:
        """
        Lists backups in the remote store

        :param remote_key: the remote key (filename)
        :param backend: the backend to use
        :param bucket_name: the name of the bucket/store
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: a list of dictionaries that contain the keys "last_modified", "version_id", and "size"
        """
        results = backend.versions(remote_key=remote_key,
                                   bucket_name=bucket_name,
                                   raise_on_error=raise_on_error)

        return results

    @staticmethod
    def pull_backup(backup_version: str, out_file: str, remote_key: str,
                    backend: AbstractBackend, bucket_name: str,
                    raise_on_error: bool = False) -> Path | None:
        """
        Pull a backup object from the remote store

        :param backup_version: the version ID of the backup to pull
        :param out_file: the output file/download location
        :param remote_key: the remote key (filename)
        :param backend: the backend to use
        :param bucket_name: the name of the bucket/store
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: a pathlib.Path object pointing to the downloaded file or None
        """
        logger = log.get_logger('caretaker')

        out_file = file.normalize_path(out_file)

        try:
            download = backend.download_object(local_file=out_file,
                                               remote_key=remote_key,
                                               version_id=backup_version,
                                               bucket_name=bucket_name,
                                               raise_on_error=raise_on_error
                                               )
            if download:

                return out_file
            else:
                raise FrontendError
        except (ClientError, FrontendError) as ce:
            logger.error('Unable to download version {} of {} to {}'.format(
                backup_version,
                remote_key,
                out_file
            ))

            if raise_on_error:
                raise ce

            return None

    @staticmethod
    def push_backup(backup_local_file: str, remote_key: str,
                    backend: AbstractBackend, bucket_name: str,
                    raise_on_error: bool = False,
                    check_identical: bool = True) -> StoreOutcome:
        """
        Push a backup to the remote store

        :param backup_local_file: the local file to push
        :param remote_key: the remote key (filename)
        :param backend: the backend to use
        :param bucket_name: the name of the bucket/store
        :param check_identical: check whether the file exists in the remote store
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: a StoreOutcome
        """
        logger = log.get_logger('caretaker')

        backup_local_file = file.normalize_path(backup_local_file)

        result = backend.store_object(remote_key=remote_key,
                                      bucket_name=bucket_name,
                                      local_file=backup_local_file,
                                      check_identical=check_identical,
                                      raise_on_error=raise_on_error)

        if result == StoreOutcome.STORED:
            logger.info('Stored backup ({}).'.format(remote_key))
            return result
        elif result == StoreOutcome.FAILED:
            logger.info('Failed to store backup.')
            return result
        else:
            logger.info('Last version was identical.')
            return result

    @staticmethod
    def run_backup(data_file: str = 'data.json',
                   archive_file: str = 'media.zip',
                   path_list: list | None = None,
                   backend: AbstractBackend | None = None,
                   bucket_name: str | None = None,
                   raise_on_error: bool = False) -> (Path | None,
                                                     Path | None):
        """
        Creates a backup set and pushes it to the remote store

        :param data_file: the output data file (e.g. data.json)
        :param archive_file: the output archive file (e.g. media.zip)
        :param path_list: the list of paths to bundle in the zip
        :param backend: the backend to use
        :param bucket_name: the name of the bucket/store
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: 2-tuple of pathlib.Path objects to the data file & archive file
        """
        logger = log.get_logger('caretaker-django')

        path_list = path_list if path_list else []

        # set up a temporary directory
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            # create a local backup set in this temporary directory
            json_file, zip_file = DjangoFrontend.create_backup(
                output_directory=temporary_directory_name,
                path_list=path_list
            )

            # push the data
            DjangoFrontend.push_backup(backup_local_file=json_file,
                                       remote_key=data_file,
                                       backend=backend, bucket_name=bucket_name,
                                       raise_on_error=raise_on_error)
            DjangoFrontend.push_backup(backup_local_file=zip_file,
                                       remote_key=archive_file,
                                       backend=backend, bucket_name=bucket_name,
                                       raise_on_error=raise_on_error)

            logger.info('Pushed backups to remote store')
            return json_file, archive_file
