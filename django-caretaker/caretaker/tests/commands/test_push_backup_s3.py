import tempfile

from django.test import TestCase
from moto import mock_s3

from caretaker.backend.abstract_backend import StoreOutcome
from caretaker.tests.utils import setup_test_class_s3, upload_temporary_file


@mock_s3
class TestPushBackup(TestCase):
    def setUp(self):
        setup_test_class_s3(self)
        self.logger.info('Setup for push_backup')

    def tearDown(self):
        self.logger.info('Teardown for push_backup')
        pass

    def test_push(self):
        self.logger.info('Testing push_backup')

        with tempfile.TemporaryDirectory() as temporary_directory_name:

            # set up a temporary file
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents=self.test_contents)

            self.assertTrue(result == StoreOutcome.STORED)

            # run a second time and should not store the result
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents=self.test_contents)

            self.assertTrue(result == StoreOutcome.IDENTICAL)

            # now test that when we add a new file it versions it
            with temporary_file.open('w') as out_file:
                out_file.write('test2')

            result = self.command.push_backup(
                backup_local_file=temporary_file, remote_key=self.json_key,
                backend=self.backend, bucket_name=self.bucket_name)

            self.assertTrue(result == StoreOutcome.STORED)
