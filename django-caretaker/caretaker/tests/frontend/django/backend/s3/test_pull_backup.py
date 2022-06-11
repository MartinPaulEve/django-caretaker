import tempfile
from pathlib import Path

from moto import mock_s3

from caretaker.utils import file
from caretaker.backend.abstract_backend import StoreOutcome
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test
from caretaker.tests.utils import upload_temporary_file, \
    file_in_zip
from caretaker.utils.zip import create_zip_file


@mock_s3
class TestPullBackupDjangoS3(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for pull_backup S3')

        self.create_bucket()

    def tearDown(self):
        self.logger.info('Teardown for pull_backup S3')
        pass

    def test(self):
        self.logger.info('Testing pull_backup S3')
        with tempfile.TemporaryDirectory() as temporary_directory_name:

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

            # delete the zip file locally
            zip_file.unlink(missing_ok=True)
            self.assertFalse(zip_file.exists())

            # list the results to get a versionId
            result = self.frontend.list_backups(
                remote_key=self.data_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            data_download_location = temporary_directory_name / self.json_key

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
