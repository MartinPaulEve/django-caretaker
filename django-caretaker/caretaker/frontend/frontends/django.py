import io
import logging
import tempfile
from io import StringIO
from pathlib import Path

from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management import call_command

from caretaker.backend.abstract_backend import AbstractBackend, StoreOutcome
from caretaker.frontend.abstract_frontend import AbstractFrontend, FrontendError
from caretaker.utils import log, file
from caretaker.utils.zip import create_zip_file


def get_frontend():
    return DjangoFrontend()


class DjangoFrontend(AbstractFrontend):
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
                      path_list: list | None = None) -> (Path | None,
                                                         Path | None):
        """
        Creates a set of local backup files

        :param output_directory: the output location
        :param data_file: the output data file (e.g. data.json)
        :param archive_file: the output archive file (e.g. media.zip)
        :param path_list: the list of paths to bundle in the zip
        :return: a 2-tuple of pathlib.Path objects to the data file and archive file
        """
        logger = log.get_logger('caretaker')

        if not output_directory:
            logger.error('No output directory specified')
            return None, None

        output_directory = file.normalize_path(output_directory)

        # create the directory if needed
        output_directory.mkdir(parents=True, exist_ok=True)

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
            path_list.append(settings.MEDIA_ROOT)

        if hasattr(settings, 'ADDITIONAL_BACKUP_PATHS') \
                and settings.CARETAKER_ADDITIONAL_BACKUP_PATHS \
                and settings.CARETAKER_ADDITIONAL_BACKUP_PATHS not in path_list:
            path_list.extend(settings.CARETAKER_ADDITIONAL_BACKUP_PATHS)

        path_list_final = [Path(path).expanduser().resolve(strict=True)
                           for path in path_list]

        zip_file = create_zip_file(
            input_paths=path_list_final,
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

        download = backend.download_object(local_file=out_file,
                                           remote_key=remote_key,
                                           version_id=backup_version,
                                           bucket_name=bucket_name,
                                           raise_on_error=raise_on_error
                                           )

        try:
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

        match result:
            case StoreOutcome.STORED:
                logger.info('Stored backup.')
            case StoreOutcome.FAILED:
                logger.info('Failed to store backup.')
            case StoreOutcome.IDENTICAL:
                logger.info('Last version was identical.')

        return result

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
            json_file, zip_file = DjangoFrontend.create_backup(
                output_directory=temporary_directory_name,
                path_list=path_list
            )

            # push the data
            DjangoFrontend.push_backup(backup_local_file=json_file,
                                       remote_key=data_file,
                                       backend=backend, bucket_name=bucket_name)
            DjangoFrontend.push_backup(backup_local_file=zip_file,
                                       remote_key=archive_file,
                                       backend=backend, bucket_name=bucket_name)

            logger.info('Pushed backups to remote store')
            return json_file, archive_file
