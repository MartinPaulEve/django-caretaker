import tempfile

from django.test import TestCase
from moto import mock_s3

from list_backups import Command as ListCommand
from tests.utils import setup_bucket, upload_temporary_file


@mock_s3
class TestListBackups(TestCase):
    def setUp(self):
        setup_bucket(self)

        self.logger.info('Setup list_backups')

        self.list_command = ListCommand()

    def tearDown(self):
        self.logger.info('Teardown list_backups')
        pass

    def test_list(self):
        self.logger.info('Testing list_backups')
        with tempfile.TemporaryDirectory() as temporary_directory_name:

            # first test that we get nothing back
            result = self.list_command._list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                s3_client=self.client
            )

            self.assertIsNone(result)

            # run the first time to store the result
            upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents=self.test_contents)

            # Now check that we get a result
            result = self.list_command._list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                s3_client=self.client
            )

            self.assertIsNotNone(result)
            version = None

            if result:
                self.assertTrue(result[0]['Size'] == 4)
                self.assertTrue(result[0]['Key'] == self.json_key)
                version = result[0]['VersionId']

            # now test that when we add a new file it versions it
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents='test2')

            # first test that we get nothing back
            result = self.list_command._list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                s3_client=self.client
            )

            self.assertIsNotNone(result)

            if result:
                self.assertTrue(result[0]['Size'] == 5)
                self.assertTrue(result[0]['Key'] == self.json_key)
                self.assertFalse(result[0]['VersionId'] == 'null')
                self.assertFalse(version == result[0]['VersionId'])
                version = result[0]['VersionId']

            # now run a final time with the same version and check that
            # the latest version is the same
            self.command._push_backup(
                backup_local_file=temporary_file, remote_key=self.json_key,
                s3_client=self.client, bucket_name=self.bucket_name)

            result = self.list_command._list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                s3_client=self.client
            )

            self.assertIsNotNone(result)

            if result:
                self.assertTrue(
                    result[0]['VersionId'] == version)
