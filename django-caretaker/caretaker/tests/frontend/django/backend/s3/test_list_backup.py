import tempfile
from unittest.mock import patch

import botocore.exceptions
from moto import mock_s3

from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test
from caretaker.tests.utils import upload_temporary_file, boto3_error


@mock_s3
class TestListBackupsDjangoS3(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup list_backups S3')

        self.create_bucket()

    def tearDown(self):
        self.logger.info('Teardown list_backups S3')
        pass

    def test(self):
        self.logger.info('Testing list_backups S3')
        with tempfile.TemporaryDirectory() as temporary_directory_name:

            # first test that we get nothing back
            result = self.frontend.list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            self.assertListEqual(result, [])

            # run the first time to store the result
            upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents=self.test_contents)

            # Now check that we get a result
            result = self.frontend.list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            self.assertIsNotNone(result)

            self.assertTrue(result[0]['size'] == 4)
            version = result[0]['version_id']

            # now test that when we add a new file it versions it
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents='test2')

            # first test that we get nothing back
            result = self.frontend.list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            self.assertIsNotNone(result)

            self.assertTrue(result[0]['size'] == 5)
            self.assertFalse(result[0]['version_id'] == 'null')
            self.assertFalse(version == result[0]['version_id'])
            version = result[0]['version_id']

            # now run a final time with the same version and check that
            # the latest version is the same
            self.frontend.push_backup(
                backup_local_file=temporary_file, remote_key=self.json_key,
                backend=self.backend, bucket_name=self.bucket_name)

            result = self.frontend.list_backups(
                remote_key=self.json_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            self.assertIsNotNone(result)

            self.assertTrue(result[0]['version_id'] == version)

            # patch for error handling
            with patch(
                    'botocore.client.BaseClient._make_api_call',
                    side_effect=boto3_error('upload_file')):

                # test raises on error
                with self.assertRaises(botocore.exceptions.ClientError):
                    result = self.frontend.list_backups(
                        remote_key=self.json_key, bucket_name=self.bucket_name,
                        backend=self.backend, raise_on_error=True
                    )

                # test returns silent empty list
                result = self.frontend.list_backups(
                    remote_key=self.json_key, bucket_name=self.bucket_name,
                    backend=self.backend
                )

                self.assertEqual(result, [])
