import tempfile
from unittest.mock import patch

import botocore.exceptions
from django.conf import settings
from moto import mock_s3

from caretaker.backend.abstract_backend import BackendFactory
from caretaker.tests.frontend.django.backend.local.caretaker_test import \
    AbstractDjangoLocalTest
from caretaker.tests.utils import upload_temporary_file


@mock_s3
class TestListBackupsDjangoLocal(AbstractDjangoLocalTest):
    def setUp(self):
        self.logger.info('Setup list_backups local')

    def tearDown(self):
        self.logger.info('Teardown list_backups local')
        pass

    def test(self):
        self.logger.info('Testing list_backups local')

        with tempfile.TemporaryDirectory() as bucket_store:

            with tempfile.TemporaryDirectory() as temporary_directory_name:
                settings.CARETAKER_LOCAL_STORE_DIRECTORY = bucket_store
                self.backend = BackendFactory.get_backend('Local')

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

                print(result)

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
                        're.search',
                        side_effect=OSError('oh dear how sad never mind')):

                    # test raises on error
                    with self.assertRaises(OSError):
                        result = self.frontend.list_backups(
                            remote_key=self.json_key,
                            bucket_name=self.bucket_name,
                            backend=self.backend, raise_on_error=True
                        )

                    # test returns silent empty list
                    result = self.frontend.list_backups(
                        remote_key=self.json_key, bucket_name=self.bucket_name,
                        backend=self.backend
                    )

                    self.assertEqual(result, [])
