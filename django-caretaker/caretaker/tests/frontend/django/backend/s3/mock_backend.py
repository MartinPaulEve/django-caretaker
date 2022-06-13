import filecmp
import importlib
import io
import logging
import tempfile
from pathlib import Path
from types import ModuleType

import boto3
import botocore.exceptions
from django.conf import settings
from moto import mock_s3

from caretaker.utils import log
from caretaker.backend.abstract_backend import AbstractBackend, StoreOutcome


def get_backend():
    return MockS3Backend()


@mock_s3
class MockS3Backend(AbstractBackend):
    @property
    def terraform_files(self) -> list[str]:
        return ['main.tf', 'output.tf']

    @property
    def terraform_template_module(self) -> ModuleType:
        """
        The directory that stores this backend's templates

        :return: a pathlib.Path to the backend's templates'
        """
        return importlib.import_module(
            'caretaker.backend.backends.terraform_aws')

    def __init__(self, logger: logging.Logger | None = None):
        super().__init__(logger)

        self.logger = log.get_logger('caretaker-amazon-s3')

        self.s3 = boto3.client(
            's3',
            aws_access_key_id='mock_key',
            aws_secret_access_key='mock_secret')

    @property
    def backend_name(self) -> str:
        """
        The display name of the backend

        :return: a string of the backend name
        """
        return 'Mock S3'

    def versions(self, bucket_name: str, remote_key: str = '',
                 raise_on_error: bool = False) -> list[dict]:
        """
        List the versions of an object in an S3 bucket

        :param remote_key: the remote key (filename) to list
        :param bucket_name: the remote bucket name
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: a list of dictionaries containing 'version_id', 'last_modified', and 'size'
        """
        return []

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
        return StoreOutcome.STORED

    def get_object(self, bucket_name: str, remote_key: str,
                   version_id: str) -> io.BytesIO | None:
        """
        Retrieve an object from the remote store as bytes

        :param bucket_name: the remote bucket name
        :param remote_key: the remote key (filename) of the object
        :param version_id: the version ID to fetch
        :return: the bytes of the retrieved object
        """
        return None

    def download_object(self, local_file: Path, bucket_name: str,
                        remote_key: str, version_id: str) -> bool:
        """
        Retrieve an object from the remote store and save it to a file

        :param local_file: the location to store the local file
        :param bucket_name: the remote bucket name
        :param remote_key: the remote key (filename) of the object
        :param version_id: the version ID to fetch
        :return: a true/false boolean of success
        """
        return False
