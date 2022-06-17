import filecmp
import importlib
import io
import logging
import tempfile
from pathlib import Path
from types import ModuleType

import boto3
import botocore.exceptions
from boto3.exceptions import S3UploadFailedError
from django.conf import settings

from caretaker.utils import log
from caretaker.backend.abstract_backend import AbstractBackend, StoreOutcome


def get_backend():
    return S3Backend()


class S3Backend(AbstractBackend):
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

        self.logger = log.get_logger('amazon-s3')

        self.client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    @property
    def backend_name(self) -> str:
        """
        The display name of the backend

        :return: a string of the backend name
        """
        return 'Amazon S3'

    def versions(self, bucket_name: str, remote_key: str = '',
                 raise_on_error: bool = False) -> list[dict]:
        """
        List the versions of an object in an S3 bucket

        :param remote_key: the remote key (filename) to list
        :param bucket_name: the remote bucket name
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: a list of dictionaries containing 'version_id', 'last_modified', and 'size'
        """
        try:
            versions = self.client.list_object_versions(Bucket=bucket_name,
                                                        Prefix=remote_key)

            if versions and 'Versions' in versions:
                final_versions = [
                    {'version_id': item['VersionId'],
                     'last_modified': item['LastModified'],
                     'size': item['Size']
                     } for item in versions['Versions']
                ]
                return final_versions
            else:
                return []
        except botocore.exceptions.ClientError as ce:
            self.logger.error(
                'Unable to retrieve version list of {} from {} in {} '
                '({})'.format(remote_key, bucket_name, self.backend_name, ce)
            )

            if raise_on_error:
                raise ce

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

        if check_identical:
            # download the latest version of the backup to see if it's the same
            # as the local file
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / 'latest'

                    self.client.download_file(Filename=str(path),
                                              Bucket=bucket_name,
                                              Key=remote_key)

                    # byte-by-byte comparison
                    # may be slow on big files
                    if filecmp.cmp(path, local_file):
                        self.logger.info(
                            'Latest backup is equal to remote S3 version')
                        return StoreOutcome.IDENTICAL

            except botocore.exceptions.ClientError:
                self.logger.debug('There was a problem comparing the previous '
                                  'version of this object with the stored '
                                  'version. This is not a fatal error and '
                                  'can be caused by this being the first '
                                  'stored version of an object.')

        try:
            # upload the latest version to S3
            self.client.upload_file(Filename=str(local_file),
                                    Bucket=bucket_name, Key=remote_key)

            self.logger.info('Backup {} stored as {}'.format(
                local_file, remote_key))
        except (botocore.exceptions.ClientError, S3UploadFailedError) as ce:
            self.logger.error('There was a problem storing the backup.')
            if raise_on_error:
                raise ce
            return StoreOutcome.FAILED

        return StoreOutcome.STORED

    def get_object(self, bucket_name: str, remote_key: str,
                   version_id: str,
                   raise_on_error: bool = False) -> io.BytesIO | None:
        """
        Retrieve an object from the remote store as bytes

        :param bucket_name: the remote bucket name
        :param remote_key: the remote key (filename) of the object
        :param version_id: the version ID to fetch
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: the bytes of the retrieved object
        """
        try:
            self.logger.info('Fetching version {} of {}'.format(
                version_id,
                remote_key
            ))

            response_object = io.BytesIO()

            self.client.download_fileobj(Bucket=bucket_name,
                                         Key=remote_key,
                                         Fileobj=response_object,
                                         ExtraArgs={'VersionId': version_id})

            response_object.seek(0)

            return response_object

        except botocore.exceptions.ClientError as ce:
            self.logger.error('Unable to download version {} of '
                              '{}'.format(version_id, remote_key))

            if raise_on_error:
                raise ce

            return None

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

        # normalize path
        out_file = Path(local_file).expanduser()

        try:
            self.client.download_file(Filename=str(out_file),
                                      Bucket=bucket_name,
                                      Key=remote_key,
                                      ExtraArgs={'VersionId': version_id})

            self.logger.info('Saved version {} of {} to {}'.format(
                version_id,
                remote_key,
                out_file
            ))

            return True
        except botocore.exceptions.ClientError as ce:
            self.logger.error('Unable to download version {} of '
                              '{} to {}'.format(version_id, remote_key,
                                                out_file))

            if raise_on_error:
                raise ce

            return False
