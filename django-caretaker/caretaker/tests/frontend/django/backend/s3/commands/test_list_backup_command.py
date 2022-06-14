import tempfile

from moto import mock_s3

from caretaker.backend.abstract_backend import StoreOutcome
from caretaker.management.commands import list_backups
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test
from caretaker.tests.utils import upload_temporary_file


@mock_s3
class TestListBackupDjangoS3Command(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for Terraform command test')

        self.create_bucket()

    def tearDown(self):
        self.logger.info('Teardown Terraform command test')
        pass

    def test(self):
        self.logger.info('Running Terraform command test')
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

            version = result[0]['version_id']

            with self.assertLogs(level='INFO') as log:
                list_backups.command.callback(
                    remote_key=self.json_key,
                    backend_name=self.backend.backend_name,
                    frontend_name=self.frontend.frontend_name
                )

                # test that the file is echoed the console log
                self.assertIn(version, ''.join(log.output))

            # now test for loaders failing
            with self.assertLogs(level='ERROR') as log:
                list_backups.command.callback(
                    remote_key=self.json_key,
                    backend_name='NON',
                    frontend_name=self.frontend.frontend_name
                )
                self.assertIn('Unable to find a valid backend',
                              ''.join(log.output))

            with self.assertLogs(level='ERROR') as log:
                list_backups.command.callback(
                    remote_key=self.json_key,
                    backend_name=self.backend.backend_name,
                    frontend_name='NON'
                )
                self.assertIn('Unable to find a valid frontend',
                              ''.join(log.output))

            return
