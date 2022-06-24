import tempfile
from unittest.mock import patch

import botocore.exceptions
from boto3.exceptions import S3UploadFailedError
from moto import mock_s3

from caretaker.backend.abstract_backend import StoreOutcome
from caretaker.tests.utils import upload_temporary_file, boto3_error
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test


@mock_s3
class TestPushBackupDjangoS3(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for push_backup')
        self.create_bucket()

    def tearDown(self):
        self.logger.info('Teardown for push_backup')

    def test(self):
        self.logger.info('Testing push_backup')

        with tempfile.TemporaryDirectory() as temporary_directory_name:

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
                    'botocore.client.BaseClient._make_api_call',
                    side_effect=boto3_error('upload_file')):
                # now test that when we add a new file it versions it
                with temporary_file.open('w') as out_file:
                    out_file.write('test3')

                    with self.assertRaises(Exception):
                        result = self.frontend.push_backup(
                            backup_local_file=temporary_file,
                            remote_key=self.json_key,
                            backend=self.backend, bucket_name=self.bucket_name,
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
