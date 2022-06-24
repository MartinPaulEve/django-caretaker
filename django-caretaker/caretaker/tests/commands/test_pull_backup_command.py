import tempfile
from pathlib import Path

from moto import mock_s3

from caretaker.backend.abstract_backend import StoreOutcome
from caretaker.management.commands import pull_backup
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test
from caretaker.tests.utils import upload_temporary_file


@mock_s3
class TestPullBackupDjangoS3Command(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for pull command test')

        self.create_bucket()

    def tearDown(self):
        self.logger.info('Teardown pull command test')
        pass

    def test(self):
        self.logger.info('Running pull command test')
        with tempfile.TemporaryDirectory() as temporary_directory_name:

            self.logger.info('Uploading temporary file')
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents=self.test_contents)

            self.assertTrue(result == StoreOutcome.STORED)

            # now grab the ID
            result = self.frontend.list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            local_file = Path(temporary_directory_name) / 'test_file.json'
            version = result[0]['version_id']

            # pull the file
            self.assertFalse(local_file.exists())
            pull_backup.command.callback(
                remote_key=self.json_key,
                local_file=local_file,
                backup_version=version,
                backend_name=self.backend.backend_name,
                frontend_name=self.frontend.frontend_name
            )
            self.assertTrue(local_file.exists())

            # pull a version that doesn't exist
            local_file.unlink()
            self.assertFalse(local_file.exists())
            pull_backup.command.callback(
                remote_key=self.json_key,
                local_file=local_file,
                backup_version=version + 'corrupt',
                backend_name=self.backend.backend_name,
                frontend_name=self.frontend.frontend_name
            )
            self.assertFalse(local_file.exists())

            # try pulling to an inaccessible local space
            local_file = Path('/sdfjlkl/') / 'test_file.json'
            self.assertFalse(local_file.exists())

            with self.assertLogs(level='ERROR') as log:
                pull_backup.command.callback(
                    remote_key=self.json_key,
                    local_file=local_file,
                    backup_version=version,
                    backend_name=self.backend.backend_name,
                    frontend_name=self.frontend.frontend_name
                )

                self.assertIn('Unable to write to {}'.format(local_file),
                              ''.join(log.output))

            # now test for loaders failing
            with self.assertLogs(level='ERROR') as log:
                pull_backup.command.callback(
                    remote_key=self.json_key,
                    local_file=local_file,
                    backup_version=version,
                    backend_name='NON',
                    frontend_name=self.frontend.frontend_name
                )
                self.assertIn('Unable to find a valid backend',
                              ''.join(log.output))

            with self.assertLogs(level='ERROR') as log:
                pull_backup.command.callback(
                    remote_key=self.json_key,
                    local_file=local_file,
                    backup_version=version,
                    backend_name=self.backend.backend_name,
                    frontend_name='NON'
                )
                self.assertIn('Unable to find a valid frontend',
                              ''.join(log.output))

            return
