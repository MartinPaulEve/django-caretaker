import tempfile
from pathlib import Path
from unittest.mock import patch

import botocore.exceptions
from django.conf import settings
from moto import mock_s3

from caretaker.utils import file
from caretaker.backend.abstract_backend import StoreOutcome, BackendFactory
from caretaker.tests.frontend.django.backend.local.caretaker_test import \
    AbstractDjangoLocalTest
from caretaker.tests.utils import upload_temporary_file, \
    file_in_zip, boto3_error
from caretaker.utils.zip import create_zip_file


@mock_s3
class TestPullBackupDjangoLocal(AbstractDjangoLocalTest):
    def setUp(self):
        self.logger.info('Setup for pull_backup local')

    def tearDown(self):
        self.logger.info('Teardown for pull_backup local')
        pass

    def test(self):
        self.logger.info('Testing pull_backup local')
        with tempfile.TemporaryDirectory() as bucket_store:

            with tempfile.TemporaryDirectory() as temporary_directory_name:

                settings.CARETAKER_LOCAL_STORE_DIRECTORY = bucket_store
                self.backend = BackendFactory.get_backend('Local')

                temporary_directory_name = file.normalize_path(
                    temporary_directory_name)

                # set up a temporary file
                result, temporary_file = upload_temporary_file(
                    test_class=self,
                    temporary_directory_name=str(temporary_directory_name),
                    contents=self.test_contents)

                self.assertTrue(result == StoreOutcome.STORED)

                # list the results to get a versionId
                result = self.frontend.list_backups(
                    remote_key=self.json_key, bucket_name=self.bucket_name,
                    backend=self.backend
                )

                download_location = temporary_directory_name / self.json_key

                result = self.frontend.pull_backup(
                    backup_version=result[0]['version_id'],
                    remote_key=self.json_key,
                    bucket_name=self.bucket_name,
                    backend=self.backend,
                    out_file=download_location
                )

                self.assertIsNotNone(result)
                self.assertTrue(download_location.exists())

                with download_location.open('r') as in_file:
                    result = in_file.read()

                    self.assertTrue(result == 'test')

                # test that we can push and pull a binary file
                zip_path = Path(temporary_directory_name) / self.data_key

                zip_file = create_zip_file(
                    input_paths=[temporary_directory_name],
                    output_file=Path(zip_path)
                )

                self.assertTrue(zip_file.exists())

                # upload the file
                self.frontend.push_backup(
                    backup_local_file=zip_file, remote_key=self.data_key,
                    backend=self.backend, bucket_name=self.bucket_name)

                # list the results to get a versionId
                result = self.frontend.list_backups(
                    remote_key=self.data_key, bucket_name=self.bucket_name,
                    backend=self.backend
                )

                data_download_location = \
                    temporary_directory_name / self.json_key

                # pull it back down
                self.frontend.pull_backup(
                    backup_version=result[0]['version_id'],
                    remote_key=self.data_key,
                    bucket_name=self.bucket_name,
                    backend=self.backend,
                    out_file=data_download_location
                )

                self.assertTrue(file_in_zip(
                    zip_file=data_download_location, filename=self.json_key
                ))

                # test the bytestream version
                bytes_response = self.frontend.pull_backup_bytes(
                    backup_version=result[0]['version_id'],
                    remote_key=self.data_key,
                    bucket_name=self.bucket_name,
                    backend=self.backend)

                bytes_read = bytes_response.read()
                with Path(zip_path).open('rb') as bytes_zip:
                    zip_read = bytes_zip.read()
                    self.assertEqual(bytes_read, zip_read)

                # patch for error handling
                with patch(
                        'caretaker.backend.backends.'
                        'local.LocalBackend._get_file_path',
                        side_effect=OSError('Oh dear how sad never mind')):

                    with self.assertRaises(OSError):
                        # test the bytestream version
                        bytes_response = self.frontend.pull_backup_bytes(
                            backup_version=result[0]['version_id'],
                            remote_key=self.data_key,
                            bucket_name=self.bucket_name,
                            backend=self.backend,
                            raise_on_error=True
                        )

                    bytes_response = self.frontend.pull_backup_bytes(
                        backup_version=result[0]['version_id'],
                        remote_key=self.data_key,
                        bucket_name=self.bucket_name,
                        backend=self.backend,
                        raise_on_error=False
                    )

                    self.assertIsNone(bytes_response)

                    with self.assertRaises(OSError):
                        self.frontend.pull_backup(
                            backup_version=result[0]['version_id'],
                            remote_key=self.data_key,
                            bucket_name=self.bucket_name,
                            backend=self.backend,
                            out_file=data_download_location,
                            raise_on_error=True
                        )

                    file_resp = self.frontend.pull_backup(
                        backup_version=result[0]['version_id'],
                        remote_key=self.data_key,
                        bucket_name=self.bucket_name,
                        backend=self.backend,
                        out_file=data_download_location,
                        raise_on_error=False
                    )

                    self.assertIsNone(file_resp)

                # delete the zip file locally
                zip_file.unlink(missing_ok=True)
                self.assertFalse(zip_file.exists())
