import tempfile
from pathlib import Path

from moto import mock_s3

from caretaker.backend.abstract_backend import StoreOutcome
from caretaker.management.commands import push_backup
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test
from caretaker.tests.utils import upload_temporary_file


@mock_s3
class TestPushBackupDjangoS3Command(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for push command test')
        self.create_bucket()

    def tearDown(self):
        self.logger.info('Teardown push command test')

    def test(self):
        self.logger.info('Running Terraform command test')
        with tempfile.TemporaryDirectory() as temporary_directory_name:

            # this local temporary file is NOT uploaded
            self.logger.info('Creating local temporary file')
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents=self.test_contents, commit=False)

            self.assertTrue(result == StoreOutcome.FAILED)

            # now call the command to upload it
            push_backup.command.callback(
                remote_key=self.json_key, local_file=temporary_file,
                backend_name=self.backend.backend_name,
                frontend_name=self.frontend.frontend_name)

            # now grab the ID
            result = self.frontend.list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            version = result[0]['version_id']

            # try uploading a non-existent file
            local_file = Path('/sdfjlkl/') / 'test_file.json'
            self.assertFalse(local_file.exists())

            with self.assertLogs(level='ERROR') as log:
                push_backup.command.callback(
                    remote_key=self.json_key, local_file=local_file,
                    backend_name=self.backend.backend_name,
                    frontend_name=self.frontend.frontend_name)

            self.assertIn('Unable to read from {}'.format(local_file),
                          ''.join(log.output))

            # now test for loaders failing
            with self.assertLogs(level='ERROR') as log:
                push_backup.command.callback(
                    remote_key=self.json_key, local_file=temporary_file,
                    backend_name='NON',
                    frontend_name=self.frontend.frontend_name)
                self.assertIn('Unable to find a valid backend',
                              ''.join(log.output))

            with self.assertLogs(level='ERROR') as log:
                push_backup.command.callback(
                    remote_key=self.json_key, local_file=temporary_file,
                    backend_name=self.backend.backend_name,
                    frontend_name='NON')
                self.assertIn('Unable to find a valid frontend',
                              ''.join(log.output))

            return
