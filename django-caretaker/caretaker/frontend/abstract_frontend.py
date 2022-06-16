import abc
import importlib
import io
import logging
import sys
from pathlib import Path
from typing import TextIO, BinaryIO

from django.conf import settings

from caretaker.backend.abstract_backend import AbstractBackend, \
    BackendFactory, StoreOutcome


class AbstractFrontend(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger

    @property
    @abc.abstractmethod
    def frontend_name(self) -> str:
        """
        The display name of the frontend

        :return: a string of the frontend name
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def export_sql(database: str = '', alternative_binary: str = '',
                   alternative_args: list | None = None,
                   output_file: str = '-') -> TextIO | BinaryIO:
        """
        Export SQL from the database using the specific provider

        :param database: the database to export
        :param alternative_binary: a different binary file to run
        :param alternative_args: a different set of cmdline args to pass
        :param output_file: an output file to write to rather than stdout
        :return: a string of the database output
        """
        pass

    @staticmethod
    @abc.abstractmethod
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
    @abc.abstractmethod
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
    @abc.abstractmethod
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
    @abc.abstractmethod
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
    @abc.abstractmethod
    def pull_backup_bytes(backup_version: str, remote_key: str,
                          backend: AbstractBackend, bucket_name: str,
                          raise_on_error: bool = False) \
            -> io.BytesIO | None:
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

    @staticmethod
    @abc.abstractmethod
    def push_backup(backup_local_file: str, remote_key: str,
                    backend: AbstractBackend, bucket_name: str,
                    raise_on_error=False,
                    check_identical: bool = True
                    ) -> StoreOutcome:
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
    @abc.abstractmethod
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
        pass


class FrontendNotFoundError (Exception):
    pass


class FrontendError(Exception):
    pass


class FrontendFactory:
    @staticmethod
    def get_frontend(frontend_name: str = '',
                     raise_on_none: bool = False) -> AbstractFrontend | None:
        """
        Return the active frontend

        :param frontend_name: the specific frontend to return. Otherwise, uses the value of CARETAKER_FRONTEND in Django settings.
        :param raise_on_none: whether to raise an exception if the frontend isn't found
        :raises FrontendNotFoundError: when the frontend is not found and raise_on_none is set to True
        :return:
        """

        # see if there's a list of backends in the settings file
        # if there is, use it
        frontends = ['caretaker.frontend.frontends.django']

        if hasattr(settings, 'CARETAKER_FRONTENDS') and \
                settings.CARETAKER_FRONTENDS:
            frontends = settings.CARETAKER_FRONTENDS

        # get the backend name in this order:
        # 1. passed to function
        # 2. passed to settings.py
        if frontend_name == '':
            frontend_name = settings.CARETAKER_FRONTEND

        # set the default frontend to Django if we're still not found
        if not frontend_name or frontend_name == '':
            frontend_name = 'Django'

        # dynamically load modules in the backends space
        for full_package_name in frontends:
            if full_package_name not in sys.modules:
                module = importlib.import_module(full_package_name)
                frontend = module.get_frontend()

                if frontend.frontend_name == frontend_name:
                    return frontend
            else:
                frontend = sys.modules[full_package_name].get_frontend()

                if frontend.frontend_name == frontend_name:
                    return frontend

        if raise_on_none:
            raise FrontendNotFoundError

        return None

    @staticmethod
    def get_frontend_and_backend(
            frontend_name: str = '',
            backend_name: str = '',
            raise_on_none: bool = False) -> (AbstractFrontend | None,
                                             AbstractBackend | None):
        """
        Return the active frontend and backend

        :param frontend_name: the name of the frontend
        :param backend_name: the name of the backend
        :param raise_on_none: whether to raise exceptions if no backend is found
        :return: 2-tuple of a frontend and backend
        """

        frontend = FrontendFactory.get_frontend(frontend_name,
                                                raise_on_none=raise_on_none)
        backend = BackendFactory.get_backend(backend_name,
                                             raise_on_none=raise_on_none)

        return frontend, backend
