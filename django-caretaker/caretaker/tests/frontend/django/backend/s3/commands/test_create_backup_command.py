import tempfile
from pathlib import Path

import django
from moto import mock_s3

from caretaker.backend.abstract_backend import StoreOutcome
from caretaker.management.commands import create_backup
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test
from caretaker.tests.utils import upload_temporary_file


@mock_s3
class TestCreateBackupDjangoS3Command(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for create_backup command')

        self.create_bucket()

        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for create_backup command')
        pass

    def test(self):
        self.logger.info('Testing create_backup command')

        with tempfile.TemporaryDirectory() as temporary_directory_name:
            # set up a temporary file
            self.logger.info('Uploading temporary file')
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents=self.test_contents)

            self.assertTrue(result == StoreOutcome.STORED)

            create_backup.command.callback(
                output_directory=temporary_directory_name,
                additional_files=(temporary_directory_name,)
            )

            json_file = Path(temporary_directory_name) / self.json_key
            data_file = Path(temporary_directory_name) / self.data_key

            self.assertTrue(json_file.exists())
            self.assertTrue(data_file.exists())

            create_backup.command.callback(
                output_directory=temporary_directory_name,
                additional_files=[temporary_directory_name],
                frontend_name='NOT FOUND'
            )
