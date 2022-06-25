import subprocess
import tempfile
from pathlib import Path

import django
from django.conf import settings
from moto import mock_s3

from caretaker.backend.abstract_backend import StoreOutcome
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test
from caretaker.tests.utils import upload_temporary_file, file_in_zip, \
    captured_output


@mock_s3
class TestCreateBackupDjangoS3(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for create_backup')

        self.create_bucket()

        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for create_backup')
        pass

    def test(self):
        self.logger.info('Testing create_backup')

        with tempfile.TemporaryDirectory() as temporary_directory_name:
            # set up a temporary file
            self.logger.info('Uploading temporary file')
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents=self.test_contents)

            self.assertTrue(result == StoreOutcome.STORED)

            # create a backup record including this directory
            json_file, data_file = self.frontend.create_backup(
                output_directory=temporary_directory_name,
                path_list=[temporary_directory_name]
            )

            self.assertTrue(json_file.exists())
            self.assertTrue(data_file.exists())

            # check error handling
            with self.assertRaises(FileNotFoundError):
                json_file, data_file = self.frontend.create_backup(
                    output_directory='',
                    path_list=[temporary_directory_name],
                    raise_on_error=True
                )

            settings.MEDIA_ROOT = ''
            settings.CARETAKER_ADDITIONAL_BACKUP_PATHS = []


            json_file, data_file = self.frontend.create_backup(
                output_directory='',
                path_list=[temporary_directory_name],
                raise_on_error=False
            )

            self.assertIsNone(json_file)
            self.assertIsNone(data_file)

            # now inject a dead media root into settings
            settings.MEDIA_ROOT = '/deadpath'

            with self.assertRaises(FileNotFoundError):
                json_file, data_file = self.frontend.create_backup(
                    output_directory=temporary_directory_name,
                    path_list=[temporary_directory_name], raise_on_error=True
                )

            tmp_filename = 'new.file'

            with tempfile.TemporaryDirectory() as temporary_directory_name_two:
                settings.MEDIA_ROOT = temporary_directory_name_two

                with (Path(temporary_directory_name) /
                      tmp_filename).open('w') as out_file:

                    out_file.write('test')

                with captured_output() as (stdout, stderr):
                    json_file, data_file = self.frontend.create_backup(
                        output_directory=temporary_directory_name,
                        path_list=[temporary_directory_name]
                    )

                    # test the post-hook execute
                    stdout_value = stdout.getvalue()
                    self.assertIn('hello /home/martin/caretaker_bucket',
                                  stdout_value)

                    self.assertIn('just_hello',
                                  stdout_value)

                self.assertTrue(file_in_zip(zip_file=data_file,
                                            filename=tmp_filename))

                # test various other aspects of post-hook execution
                del settings.CARETAKER_POST_EXECUTE

                # just check this runs
                with captured_output() as (stdout, stderr):
                    json_file, data_file = self.frontend.create_backup(
                        output_directory=temporary_directory_name,
                        path_list=[temporary_directory_name]
                    )

                settings.CARETAKER_POST_EXECUTE = ['COMMAND_DOES_NOT_EXIST']

                with captured_output() as (stdout, stderr):
                    with self.assertRaises(FileNotFoundError):
                        json_file, data_file = self.frontend.create_backup(
                            output_directory=temporary_directory_name,
                            path_list=[temporary_directory_name]
                        )

                settings.CARETAKER_POST_EXECUTE = ['false']

                with captured_output() as (stdout, stderr):
                    with self.assertRaises(subprocess.CalledProcessError):
                        json_file, data_file = self.frontend.create_backup(
                            output_directory=temporary_directory_name,
                            path_list=[temporary_directory_name]
                        )

                # cleanup
                del settings.CARETAKER_POST_EXECUTE

            settings.MEDIA_ROOT = ''

            with tempfile.TemporaryDirectory() as temporary_directory_name_two:
                settings.CARETAKER_ADDITIONAL_BACKUP_PATHS = \
                    [temporary_directory_name_two]

                with (Path(temporary_directory_name) /
                      tmp_filename).open('w') as out_file:

                    out_file.write('test')

                    json_file, data_file = self.frontend.create_backup(
                        output_directory=temporary_directory_name,
                        path_list=[temporary_directory_name]
                    )

                    self.assertTrue(file_in_zip(zip_file=data_file,
                                                filename=tmp_filename))
