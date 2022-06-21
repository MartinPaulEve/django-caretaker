import tempfile
from unittest.mock import patch

from django.conf import settings
from moto import mock_s3

from caretaker.backend.abstract_backend import StoreOutcome, BackendFactory
from caretaker.tests.frontend.django.backend.local.caretaker_test import \
    AbstractDjangoLocalTest
from caretaker.tests.utils import upload_temporary_file, boto3_error


@mock_s3
class TestPushBackupDjangoLocal(AbstractDjangoLocalTest):
    def setUp(self):
        self.logger.info('Setup for push_backup')

    def tearDown(self):
        self.logger.info('Teardown for push_backup')

    def test(self):
        self.logger.info('Testing push_backup')

        with tempfile.TemporaryDirectory() as bucket_store:

            with tempfile.TemporaryDirectory() as temporary_directory_name:

                settings.CARETAKER_LOCAL_STORE_DIRECTORY = bucket_store
                self.backend = BackendFactory.get_backend('Local')

                # set up a temporary file
                result, temporary_file = upload_temporary_file(
                    test_class=self,
                    temporary_directory_name=temporary_directory_name,
                    contents=self.test_contents, check_identical=False)

                self.assertTrue(result == StoreOutcome.STORED)

                # run a second time and should not store the result
                result, temporary_file = upload_temporary_file(
                    test_class=self,
                    temporary_directory_name=temporary_directory_name,
                    contents=self.test_contents)

                self.assertTrue(result == StoreOutcome.IDENTICAL)

                # now test that when we add a new file it versions it
                with temporary_file.open('w') as out_file:
                    out_file.write('test2')

                result = self.frontend.push_backup(
                    backup_local_file=temporary_file, remote_key=self.json_key,
                    backend=self.backend, bucket_name=self.bucket_name)

                self.assertTrue(result == StoreOutcome.STORED)

                # test the error
                with patch(
                        'caretaker.backend.backends.'
                        'local.LocalBackend._create_file_path',
                        side_effect=OSError('Oh dear how sad never mind')):
                    # now test that when we add a new file it versions it
                    with temporary_file.open('w') as out_file:
                        out_file.write('test3')

                        with self.assertRaises(OSError):
                            result = self.frontend.push_backup(
                                backup_local_file=temporary_file,
                                remote_key=self.json_key,
                                backend=self.backend,
                                bucket_name=self.bucket_name,
                                raise_on_error=True
                            )

                        # now test without raise on error
                        result = self.frontend.push_backup(
                            backup_local_file=temporary_file,
                            remote_key=self.json_key,
                            backend=self.backend, bucket_name=self.bucket_name,
                            raise_on_error=False
                        )

                    self.assertEqual(result, StoreOutcome.FAILED)
