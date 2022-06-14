import tempfile
from pathlib import Path

from django.conf import settings
from moto import mock_s3

from caretaker.utils import file
from caretaker.backend.abstract_backend import StoreOutcome
from caretaker.management.commands import run_backup
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test
from caretaker.tests.utils import upload_temporary_file


@mock_s3
class TestRunBackupDjangoS3Command(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for pull command test')

        self.create_bucket()

    def tearDown(self):
        self.logger.info('Teardown pull command test')
        pass

    def test(self):
        self.logger.info('Running pull command test')
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            temporary_directory_name = file.normalize_path(
                temporary_directory_name)

            # set up a temporary file
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=str(temporary_directory_name),
                contents=self.test_contents)

            self.assertTrue(result == StoreOutcome.STORED)

            settings.MEDIA_ROOT = ''
            settings.CARETAKER_ADDITIONAL_BACKUP_PATHS = []

            # run the backup
            run_backup.command.callback(
                output_directory='',
                additional_files=(temporary_directory_name,),
                backend_name=self.backend.backend_name,
                frontend_name=self.frontend.frontend_name
            )

            # now grab the ID
            result = self.frontend.list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            version = result[0]['version_id']
            self.assertIsNotNone(version)

            # now test for loaders failing
            with self.assertLogs(level='ERROR') as log:
                run_backup.command.callback(
                    output_directory='',
                    additional_files=(temporary_directory_name,),
                    backend_name='NON',
                    frontend_name=self.frontend.frontend_name
                )
                self.assertIn('Unable to find a valid backend',
                              ''.join(log.output))

            with self.assertLogs(level='ERROR') as log:
                run_backup.command.callback(
                    output_directory='',
                    additional_files=(temporary_directory_name,),
                    backend_name=self.backend.backend_name,
                    frontend_name='NON'
                )
                self.assertIn('Unable to find a valid frontend',
                              ''.join(log.output))

            return






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
