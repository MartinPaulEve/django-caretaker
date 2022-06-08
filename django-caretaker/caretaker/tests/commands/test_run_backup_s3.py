import json
import tempfile
from pathlib import Path

import django
from django.test import TestCase
from moto import mock_s3

from caretaker.backend.abstract_backend import StoreOutcome
from caretaker.management.commands.list_backups import Command as ListCommand
from caretaker.management.commands.pull_backup import Command as PullCommand
from caretaker.management.commands.run_backup import Command as RunCommand
from caretaker.tests.utils import setup_test_class_s3, upload_temporary_file, \
    file_in_zip


@mock_s3
class TestRunBackup(TestCase):
    def setUp(self):
        setup_test_class_s3(self)

        self.logger.info('Setup for run_backup S3')

        self.run_command = RunCommand()
        self.pull_command = PullCommand()
        self.list_command = ListCommand()

        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for run_backup S3')
        pass

    def test_run(self):
        self.logger.info('Testing run_backup S3')

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
            self.run_command.run_backup(
                output_directory=temporary_directory_name,
                path_list=[temporary_directory_name],
                bucket_name=self.bucket_name,
                backend=self.backend
            )

            # now check that the files exist in S3
            # list the results to get a versionId of the SQL backup
            result = self.list_command.list_backups(
                remote_key=self.dump_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            Path(temporary_directory_name / self.json_key).unlink(
                missing_ok=True)
            download_location = temporary_directory_name / self.json_key

            result = self.pull_command.pull_backup(
                backup_version=result[0]['version_id'],
                remote_key=self.dump_key,
                bucket_name=self.bucket_name,
                backend=self.backend,
                out_file=download_location
            )

            with result.open('r') as in_file:
                response = in_file.read()

                try:
                    json.loads(response)
                except json.JSONDecodeError:
                    self.fail('The stored object could not be JSON decoded')

            # now check the archive zip
            result = self.list_command.list_backups(
                remote_key=self.data_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            Path(temporary_directory_name / self.data_key).unlink(
                missing_ok=True)
            download_location = temporary_directory_name / self.data_key

            result = self.pull_command.pull_backup(
                backup_version=result[0]['version_id'],
                remote_key=self.data_key,
                bucket_name=self.bucket_name,
                backend=self.backend,
                out_file=download_location
            )

            self.assertTrue(file_in_zip(zip_file=result,
                                        filename=self.json_key))
