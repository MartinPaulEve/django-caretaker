import tempfile

from django.test import TestCase
from moto import mock_s3

from caretaker.management.commands.list_backups import Command as ListCommand
from caretaker.tests.utils import setup_test_class_s3, upload_temporary_file


@mock_s3
class TestListBackups(TestCase):
    def setUp(self):
        setup_test_class_s3(self)

        self.logger.info('Setup list_backups S3')

        self.list_command = ListCommand()

    def tearDown(self):
        self.logger.info('Teardown list_backups S3')
        pass

    def test_list(self):
        self.logger.info('Testing list_backups S3')
        with tempfile.TemporaryDirectory() as temporary_directory_name:

            # first test that we get nothing back
            result = self.list_command.list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            self.assertListEqual(result, [])

            # run the first time to store the result
            upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents=self.test_contents)

            # Now check that we get a result
            result = self.list_command.list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            self.assertIsNotNone(result)
            version = None

            if result:
                self.assertTrue(result[0]['size'] == 4)
                version = result[0]['version_id']

            # now test that when we add a new file it versions it
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents='test2')

            # first test that we get nothing back
            result = self.list_command.list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            self.assertIsNotNone(result)

            if result:
                self.assertTrue(result[0]['size'] == 5)
                self.assertFalse(result[0]['version_id'] == 'null')
                self.assertFalse(version == result[0]['version_id'])
                version = result[0]['version_id']

            # now run a final time with the same version and check that
            # the latest version is the same
            self.command.push_backup(
                backup_local_file=temporary_file, remote_key=self.json_key,
                backend=self.backend, bucket_name=self.bucket_name)

            result = self.list_command.list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            self.assertIsNotNone(result)

            if result:
                self.assertTrue(
                    result[0]['version_id'] == version)
