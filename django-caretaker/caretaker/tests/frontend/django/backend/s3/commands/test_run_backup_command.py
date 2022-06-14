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

            run_backup.command.callback(
                additional_files=(temporary_directory_name,),
                backend_name=self.backend.backend_name,
                frontend_name=self.frontend.frontend_name
            )

            # now test for loaders failing
            with self.assertLogs(level='ERROR') as log:
                run_backup.command.callback(
                    additional_files=(temporary_directory_name,),
                    backend_name='NON',
                    frontend_name=self.frontend.frontend_name
                )
                self.assertIn('Unable to find a valid backend',
                              ''.join(log.output))

            with self.assertLogs(level='ERROR') as log:
                run_backup.command.callback(
                    additional_files=(temporary_directory_name,),
                    backend_name=self.backend.backend_name,
                    frontend_name='NON'
                )
                self.assertIn('Unable to find a valid frontend',
                              ''.join(log.output))

            return

