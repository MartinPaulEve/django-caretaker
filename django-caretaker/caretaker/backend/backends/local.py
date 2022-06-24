import filecmp
import glob
import importlib
import io
import logging
import os.path
import re
import shutil
import time
import uuid
from pathlib import Path
from types import ModuleType

from django.conf import settings
from datetime import datetime

from caretaker.backend.abstract_backend import AbstractBackend, StoreOutcome
from caretaker.utils import log, file


def get_backend():
    return LocalBackend()


class LocalBackend(AbstractBackend):
    @property
    def terraform_files(self) -> list[str]:
        """
        The terraform files for this backend

        :return: a list of terraform files
        """
        return []

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

        self.logger = log.get_logger('local')

        self.directory_store = file.normalize_path(
            settings.CARETAKER_LOCAL_STORE_DIRECTORY)
        self.file_pattern_raw = settings.CARETAKER_LOCAL_FILE_PATTERN
        self.file_pattern_regex = settings.CARETAKER_LOCAL_FILE_PATTERN

        self.file_pattern_regex = self.file_pattern_regex.replace(
            '{{version}}',
            r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
        )

        self.file_pattern_regex = self.file_pattern_regex.replace(
            '{{date}}', r'([\d\.]+)'
        )

    @property
    def backend_name(self) -> str:
        """
        The display name of the backend

        :return: a string of the backend name
        """
        return 'Local'

    def _most_recent(self, bucket_name: str, remote_key: str = '',
                     raise_on_error: bool = False) -> dict:
        """
        Retrieve the most recent version of the file stored

        :param bucket_name: the name of the bucket
        :param remote_key: the remote key (filename) to list
        :param raise_on_error: whether to raise an exception on error
        :return: a dictionary of the most recent version of the file
        """
        versions = self.versions(bucket_name=bucket_name,
                                 remote_key=remote_key,
                                 raise_on_error=raise_on_error)

        # versions is sorted by date modified so index zero is always the most
        # recent
        return versions[0] if len(versions) > 0 else []

    def versions(self, bucket_name: str, remote_key: str = '',
                 raise_on_error: bool = False) -> list[dict]:
        """
        List the versions of an object in an S3 bucket

        :param remote_key: the remote key (filename) to list
        :param bucket_name: the directory name
        :param raise_on_error: whether to raise underlying exceptions if there is a client error
        :return: a list of dictionaries containing 'version_id', 'last_modified', and 'size'
        """
        try:
            directory_list = (Path(self.directory_store) /
                              bucket_name).glob('**/*')

            versions = []

            for file_name in directory_list:
                final_regex = '{}-{}'.format(self.file_pattern_regex,
                                             remote_key)
                match = re.search(final_regex, str(file_name))

                if match:
                    sub_version = {
                        'version_id': match.group(1),
                        'last_modified':
                            datetime.fromtimestamp(float(match.group(2))),
                        'size': os.path.getsize(file_name),
                        'file_name': file_name
                    }

                    versions.append(sub_version)

            # sort versions by last_modified in the dictionary
            versions.sort(key=lambda item: item['last_modified'], reverse=True)

            return versions
        except OSError as oe:
            if raise_on_error:
                raise oe

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
            latest = self._most_recent(bucket_name=bucket_name,
                                       remote_key=remote_key)

            if 'file_name' in latest:
                if filecmp.cmp(latest['file_name'], local_file):
                    self.logger.info(
                        'Latest backup is equal to remote S3 version')
                    return StoreOutcome.IDENTICAL

        try:
            new_path = self._create_file_path(bucket_name, remote_key)

            # create the directory if it doesn't exist
            new_path.parent.mkdir(parents=True, exist_ok=True)

            # copy the file
            shutil.copy(local_file, str(new_path))

            self.logger.info('Backup {} stored as {}'.format(
                local_file, new_path))
        except OSError as ce:
            self.logger.error('There was a problem storing the backup: '
                              '{}.'.format(ce))
            if raise_on_error:
                raise ce
            return StoreOutcome.FAILED

        return StoreOutcome.STORED

    def _create_file_path(self, bucket_name, remote_key) -> Path:
        """
        Create a file path for the backup

        :param bucket_name: the bucket name
        :param remote_key: the remote key (filename)
        :return:
        """
        file_pattern = self.file_pattern_raw.replace(
            '{{version}}', str(uuid.uuid4())
        )

        file_pattern = file_pattern.replace(
            '{{date}}', str(time.time())
        )

        new_path = Path(self.directory_store) / Path(bucket_name)
        new_path = new_path / '{}-{}'.format(file_pattern, remote_key)

        return new_path

    def _get_file_path(self, bucket_name, remote_key, version) -> Path:
        """
        Return a wildcarded/glob file pattern for the backup

        :param bucket_name: the bucket name
        :param remote_key: the remote key (filename)
        :param version: the version of the backup
        :return: a Path with a wildcard
        """
        file_pattern = self.file_pattern_raw.replace(
            '{{version}}', version
        )

        # date in this function is a glob
        file_pattern = file_pattern.replace(
            '{{date}}', '*'
        )

        new_path = Path(self.directory_store) / Path(bucket_name)
        new_path = new_path / '{}-{}'.format(file_pattern, remote_key)

        return new_path

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

            new_path = glob.glob(str(self._get_file_path(bucket_name,
                                                         remote_key,
                                                         version_id)))[0]

            with open(new_path, 'rb') as fh:
                buf = io.BytesIO(fh.read())
                buf.seek(0)
                return buf

        except OSError as ce:
            self.logger.error('Unable to retrieve version {} of '
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
        new_path = ''

        try:
            new_path = glob.glob(str(self._get_file_path(bucket_name,
                                                         remote_key,
                                                         version_id)))[0]

            shutil.copy(str(new_path), out_file)

            self.logger.info('Saved version {} of {} to {}'.format(
                version_id,
                remote_key,
                out_file
            ))

            return True
        except OSError as ce:
            self.logger.error(
                'Unable to retrieve version {} of '
                '{} to {}. Attempted to open {}.'.format(version_id,
                                                         remote_key,
                                                         out_file,
                                                         new_path))

            if raise_on_error:
                raise ce

            return False
