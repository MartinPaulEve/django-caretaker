import abc
import importlib
import logging
import sys
from enum import Enum
from pathlib import Path

from django.conf import settings


class StoreOutcome(Enum):
    FAILED = 0
    STORED = 1
    IDENTICAL = 2


class AbstractBackend(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger

    @property
    @abc.abstractmethod
    def backend_name(self) -> str:
        """
        The display name of the backend
        :return: a string of the backend name
        """
        pass

    @abc.abstractmethod
    def versions(self, bucket_name: str, remote_key: str = '') -> list[dict]:
        """
        List the versions of an object
        :param remote_key: the remote key to list
        :param bucket_name: the remote bucket name
        :return: a list of dictionaries containing 'version_id' and
        'last_modified'
        """
        pass

    @abc.abstractmethod
    def store_object(self, local_file: Path, bucket_name: str,
                     remote_key: str, check_identical: bool) -> StoreOutcome:
        """
        Store an object remotely
        :param local_file: the local file to store
        :param bucket_name: the remote bucket name
        :param remote_key: the remote key of the object
        :param check_identical: whether to check if the last version is already
        the same as this version
        :return: a response enum StoreOutcome
        """
        pass

    @abc.abstractmethod
    def get_object(self, bucket_name: str, remote_key: str,
                   version_id: str) -> bytes | None:
        """
        Retrieve an object from the remote store as bytes
        :param bucket_name: the remote bucket name
        :param remote_key: the remote key of the object
        :param version_id: the version ID to fetch
        :return: the bytes of the retrieved object
        """
        pass

    @abc.abstractmethod
    def download_object(self, local_file: Path, bucket_name: str,
                        remote_key: str, version_id: str) -> bool:
        """
        Retrieve an object from the remote store and save it to a file
        :param local_file: the location to store the local file
        :param bucket_name: the remote bucket name
        :param remote_key: the remote key of the object
        :param version_id: the version ID to fetch
        :return: a true/false boolean of success
        """
        pass


class BackendFactory:
    @staticmethod
    def get_backend(backend_name: str = '') -> AbstractBackend | None:
        # see if there's a list of backends in the settings file
        # if there is, use it
        backends = ['caretaker.backend.backends.s3']

        if hasattr(settings, 'CARETAKER_BACKENDS') and \
                settings.CARETAKER_BACKENDS:
            backends = settings.CARETAKER_BACKENDS

        # get the backend name in this order:
        # 1. passed to function
        # 2. passed to settings.py
        if backend_name == '':
            backend_name = settings.CARETAKER_BACKEND

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

        return None
