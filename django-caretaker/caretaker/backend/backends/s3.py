import filecmp
import io
import logging
import tempfile
from pathlib import Path

import boto3
import botocore.exceptions
from django.conf import settings

from caretaker.utils import log
from caretaker.backend.abstract_backend import AbstractBackend, StoreOutcome


def get_backend():
    return S3Backend()


class S3Backend(AbstractBackend):
    def __init__(self, logger: logging.Logger | None = None):
        super().__init__(logger)

        self.logger = log.get_logger('caretaker-amazon-s3')

        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    @property
    def backend_name(self) -> str:
        return 'Amazon S3'

    def versions(self, bucket_name: str, remote_key: str = '') -> list[dict]:
        try:
            versions = self.s3.list_object_versions(Bucket=bucket_name,
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
            return []

    def store_object(self, local_file: Path, bucket_name: str,
                     remote_key: str, check_identical: bool) -> StoreOutcome:

        if check_identical:
            # download the latest version of the backup to see if it's the same
            # as the local file
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / 'latest'

                    self.s3.download_file(Filename=str(path),
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
            self.s3.upload_file(Filename=str(local_file),
                                Bucket=bucket_name, Key=remote_key)

            self.logger.info('Backup {} stored as {}'.format(
                local_file, remote_key))
        except botocore.exceptions.ClientError:
            self.logger.error('There was a problem storing the backup.')
            return StoreOutcome.FAILED

        return StoreOutcome.STORED

    def get_object(self, bucket_name: str, remote_key: str,
                   version_id: str) -> io.BytesIO | None:
        try:
            self.logger.info('Fetching version {} of {}'.format(
                version_id,
                remote_key
            ))

            response_object = io.BytesIO()

            self.s3.download_fileobj(Bucket=settings.CARETAKER_BACKUP_BUCKET,
                                     Key=remote_key,
                                     Fileobj=response_object,
                                     ExtraArgs={'VersionId': version_id})

            response_object.seek(0)

            return response_object

        except botocore.exceptions.ClientError:
            self.logger.error('Unable to download version {} of '
                              '{}'.format(version_id, remote_key))
            return None

    def download_object(self, local_file: Path, bucket_name: str,
                        remote_key: str, version_id: str) -> bool:
        # normalize path
        out_file = Path(local_file).expanduser()

        try:
            self.s3.download_file(Filename=str(out_file),
                                  Bucket=bucket_name,
                                  Key=remote_key,
                                  ExtraArgs={'VersionId': version_id})

            self.logger.info('Saved version {} of {} to {}'.format(
                version_id,
                remote_key,
                out_file
            ))

            return True
        except botocore.exceptions.ClientError:
            self.logger.error('Unable to download version {} of '
                              '{} to {}'.format(version_id, remote_key,
                                                out_file))
            return False
