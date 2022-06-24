import abc
import importlib
import logging
import sys
from enum import Enum
from pathlib import Path
from types import ModuleType

from django.conf import settings


class StoreOutcome(Enum):
    FAILED = 0
    STORED = 1
    IDENTICAL = 2


class AbstractBackend(metaclass=abc.ABCMeta):
    client = None

    @abc.abstractmethod
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger

    @property
    @abc.abstractmethod
    def terraform_files(self) -> list[str]:
        pass

    @property
    @abc.abstractmethod
    def backend_name(self) -> str:
        """
        The display name of the backend

        :return: a string of the backend name
        """
        pass

    @property
    @abc.abstractmethod
    def terraform_template_module(self) -> ModuleType:
        """
        The directory that stores this backend's templates

        :return: a pathlib.Path to the backend's templates'
        """
        pass

    @abc.abstractmethod
    def versions(self, bucket_name: str, remote_key: str = '',
                 raise_on_error: bool = False) -> list[dict]:
        """
        List the versions of an object

        :param remote_key: the remote key (filename) to list
        :param bucket_name: the remote bucket name
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: a list of dictionaries containing 'version_id', 'last_modified', and 'size'
        """
        pass

    @abc.abstractmethod
    def store_object(self, local_file: Path, bucket_name: str,
                     remote_key: str, check_identical: bool,
                     raise_on_error: bool = False) -> StoreOutcome:
        """
        Store an object remotely

        :param local_file: the local file to store
        :param bucket_name: the remote bucket name
        :param remote_key: the remote key (filename) of the object
        :param check_identical: whether to check if the last version is already the same as this version
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: a response enum StoreOutcome
        """
        pass

    @abc.abstractmethod
    def get_object(self, bucket_name: str, remote_key: str,
                   version_id: str,
                   raise_on_error: bool = False) -> bytes | None:
        """
        Retrieve an object from the remote store as bytes

        :param bucket_name: the remote bucket name
        :param remote_key: the remote key (filename) of the object
        :param version_id: the version ID to fetch
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: the bytes of the retrieved object
        """
        pass

    @abc.abstractmethod
    def download_object(self, local_file: Path, bucket_name: str,
                        remote_key: str, version_id: str,
                        raise_on_error: bool = False) -> bool:
        """
        Retrieve an object from the remote store and save it to a file

        :param local_file: the location to store the local file
        :param bucket_name: the remote bucket name
        :param remote_key: the remote key (filename) of the object
        :param version_id: the version ID to fetch
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: a true/false boolean of success
        """
        pass


class BackendFactory:
    @staticmethod
    def get_backend(backend_name: str = '',
                    raise_on_none: bool = False) -> AbstractBackend | None:
        """
        Return the active backend

        :param backend_name: the specific backend to return. Otherwise, uses the value of CARETAKER_BACKEND in Django settings.
        :param raise_on_none: whether to raise an exception if the backend isn't found
        :raises BackendNotFoundError: when the backend is not found and raise_on_none is set to True
        :return:
        """

        # see if there's a list of backends in the settings file
        # if there is, use it
        backends = ['caretaker.backend.backends.s3',
                    'caretaker.backend.backends.local']

        if hasattr(settings, 'CARETAKER_BACKENDS') and \
                settings.CARETAKER_BACKENDS:
            backends = settings.CARETAKER_BACKENDS

        # get the backend name in this order:
        # 1. passed to function
        # 2. passed to settings.py
        if backend_name == '':
            backend_name = settings.CARETAKER_BACKEND

        if not backend_name or backend_name == '':
            backend_name = 'Amazon S3'

        # dynamically load modules in the backends space
        for full_package_name in backends:
            if full_package_name not in sys.modules:
                module = importlib.import_module(full_package_name)
                backend = module.get_backend()

                if backend.backend_name == backend_name:
                    return backend
            else:
                backend = sys.modules[full_package_name].get_backend()

                if backend.backend_name == backend_name:
                    return backend

        if raise_on_none:
            raise BackendNotFoundError

        return None


class BackendNotFoundError(Exception):
    pass
