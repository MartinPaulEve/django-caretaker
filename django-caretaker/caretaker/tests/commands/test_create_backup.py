import tempfile
from pathlib import Path

from django.test import TestCase
from moto import mock_s3

from create_backup import Command as CreateCommand
from tests.utils import setup_bucket, upload_temporary_file


@mock_s3
class TestCreateBackup(TestCase):
    def setUp(self):
        setup_bucket(self)

        self.logger.info('Setup for create_backup')

        self.create_command = CreateCommand()

    def tearDown(self):
        self.logger.info('Teardown for create_backup')
        pass

    def test_create(self):
        self.logger.info('Testing create_backup')

        with tempfile.TemporaryDirectory() as temporary_directory_name:
            temporary_directory_name = Path(
                temporary_directory_name).expanduser()

            # set up a temporary file
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents=self.test_contents)

            self.assertTrue(result == self.command.returns[1])

            # create a backup record including this directory
            json_file, data_file = self.create_command._create_backup(
                output_directory=temporary_directory_name,
                path_list=[temporary_directory_name]
            )

            self.assertTrue(json_file.exists())
            self.assertTrue(data_file.exists())
