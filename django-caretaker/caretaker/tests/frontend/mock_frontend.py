import io
import logging
from pathlib import Path

from caretaker.backend.abstract_backend import AbstractBackend, StoreOutcome
from caretaker.frontend.abstract_frontend import AbstractFrontend
from caretaker.utils import log


def get_frontend():
    return MockFrontend()


class MockFrontend(AbstractFrontend):
    @staticmethod
    def export_sql(database: str = '', alternative_binary: str = '',
                   alternative_args: list | None = None,
                   output_file: str = '-') -> str:
        """
        Export SQL from the database using the specific provider

        :param database: the database to export
        :param alternative_binary: a different binary file to run
        :param alternative_args: a different set of cmdline args to pass
        :param output_file: an output file to write to rather than stdout
        :return: a string of the database output
        """

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
        pass

    def __init__(self, logger: logging.Logger | None = None):
        super().__init__(logger)

        self.logger = log.get_logger('caretaker-mock-frontend')

    @property
    def frontend_name(self) -> str:
        """
        The display name of the frontend

        :return: a string of the frontend name
        """
        return 'Mock Frontend'

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
        pass

    @staticmethod
    def generate_terraform(output_directory: str,
                           backend: AbstractBackend) -> Path | None:
        """
        Generate a set of Terraform output files to provision an infrastructure

        :param output_directory: the output directory to write to
        :param backend: the backend to use
        :return: a path indicating where the Terraform files reside
        """
        pass

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
        pass

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
        pass

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
        pass

    @staticmethod
    def run_backup(output_directory: str, data_file: str = 'data.json',
                   archive_file: str = 'media.zip',
                   path_list: list | None = None,
                   backend: AbstractBackend | None = None,
                   bucket_name: str | None = None,
                   raise_on_error: bool = False) -> (Path | None,
                                                     Path | None):
        """
        Creates a backup set and pushes it to the remote store

        :param output_directory: the output directory for the local backup set
        :param data_file: the output data file (e.g. data.json)
        :param archive_file: the output archive file (e.g. media.zip)
        :param path_list: the list of paths to bundle in the zip
        :param backend: the backend to use
        :param bucket_name: the name of the bucket/store
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: 2-tuple of pathlib.Path objects to the data file & archive file
        """
        pass
