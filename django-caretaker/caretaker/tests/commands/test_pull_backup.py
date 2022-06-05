import tempfile
from pathlib import Path

from django.test import TestCase
from moto import mock_s3

from list_backups import Command as ListCommand
from pull_backup import Command as PullCommand
from tests.utils import setup_bucket, upload_temporary_file, \
    file_in_zip
from caretaker.main_utils.zip import create_zip_file


@mock_s3
class TestPullBackup(TestCase):
    def setUp(self):
        setup_bucket(self)

        self.logger.info('Setup for pull_backup')

        self.pull_command = PullCommand()
        self.list_command = ListCommand()

    def tearDown(self):
        self.logger.info('Teardown for pull_backup')
        pass

    def test_pull(self):
        self.logger.info('Testing pull_backup')
        with tempfile.TemporaryDirectory() as temporary_directory_name:

            temporary_directory_name = Path(
                temporary_directory_name).expanduser()

            # set up a temporary file
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents=self.test_contents)

            self.assertTrue(result == self.command.returns[1])

            # list the results to get a versionId
            result = self.list_command._list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                s3_client=self.client
            )

            download_location = temporary_directory_name / self.json_key

            result = self.pull_command._pull_backup(
                backup_version=result[0]['VersionId'],
                remote_key=self.json_key,
                bucket_name=self.bucket_name,
                s3_client=self.client,
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
            self.command._push_backup(
                backup_local_file=zip_file, remote_key=self.data_key,
                s3_client=self.client, bucket_name=self.bucket_name)

            # delete the zip file locally
            zip_file.unlink(missing_ok=True)
            self.assertFalse(zip_file.exists())

            # list the results to get a versionId
            result = self.list_command._list_backups(
                remote_key=self.data_key, bucket_name=self.bucket_name,
                s3_client=self.client
            )

            data_download_location = temporary_directory_name / self.json_key

            # pull it back down
            self.pull_command._pull_backup(
                backup_version=result[0]['VersionId'],
                remote_key=self.data_key,
                bucket_name=self.bucket_name,
                s3_client=self.client,
                out_file=data_download_location
            )

            self.assertTrue(file_in_zip(
                zip_file=data_download_location, filename=self.json_key
            ))
