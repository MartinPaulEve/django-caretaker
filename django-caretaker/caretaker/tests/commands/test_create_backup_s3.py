import tempfile
from pathlib import Path

import django
from django.test import TestCase
from moto import mock_s3

from caretaker.backend.abstract_backend import StoreOutcome
from caretaker.management.commands.create_backup import Command as CreateCommand
from caretaker.tests.utils import setup_test_class_s3, upload_temporary_file


@mock_s3
class TestCreateBackup(TestCase):
    def setUp(self):
        setup_test_class_s3(self)

        self.logger.info('Setup for create_backup')

        self.create_command = CreateCommand()

        django.setup()

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

            self.assertTrue(result == StoreOutcome.STORED)

            # create a backup record including this directory
            json_file, data_file = self.create_command.create_backup(
                output_directory=temporary_directory_name,
                path_list=[temporary_directory_name]
            )

            self.assertTrue(json_file.exists())
            self.assertTrue(data_file.exists())
