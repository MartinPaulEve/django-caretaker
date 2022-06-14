import tempfile

from django.contrib.auth.models import User
from django.test import RequestFactory
from moto import mock_s3

from caretaker import views
from caretaker.backend.abstract_backend import StoreOutcome
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test
from caretaker.tests.utils import upload_temporary_file


@mock_s3
class TestDjangoS3Views(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for Django S3 Views test')

        self.create_bucket()

        self.factory = RequestFactory()

        self.user = User.objects.create_superuser(username='test',
                                                  email='test@test.com',
                                                  password='top_secret')

    def tearDown(self):
        self.logger.info('Teardown Django S3 Views test')
        pass

    def test(self):
        self.logger.info('Running Django S3 Views test')

        with tempfile.TemporaryDirectory() as temporary_directory_name:
            # set up a temporary file
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents=self.test_contents, check_identical=False,
                remote_key=self.dump_key
            )

            self.assertTrue(result == StoreOutcome.STORED)
            self.logger.info('Wrote {} as {}'.format(temporary_file,
                                                     self.data_key))

            # now grab the ID
            result = self.frontend.list_backups(
                remote_key=self.dump_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            version = result[0]['version_id']

            request = self.factory.get('/list/', follow=True)
            request.user = self.user

            response = views.list_backups(request)

            # check that we have the regex in the view
            included_regex = r'\/download\/sql\/version\/{}\/'.format(version)
            self.assertRegex(response.content.decode('utf-8'), included_regex)

            # now test the download function
            url = '/download/sql/version/{}/'.format(version)
            request = self.factory.get(url, follow=True)
            request.user = self.user

            response = views.download_backup(request, backup_type='sql',
                                             version_id=version)
            self.assertEqual(response.status_code, 200)

            # now upload a media zip file
            # set up a temporary file
            result, temporary_file = upload_temporary_file(
                test_class=self,
                temporary_directory_name=temporary_directory_name,
                contents=self.test_contents, check_identical=False,
                remote_key=self.data_key
            )

            self.assertTrue(result == StoreOutcome.STORED)
            self.logger.info('Wrote {} as {}'.format(temporary_file,
                                                     self.data_key))

            # now grab the ID
            result = self.frontend.list_backups(
                remote_key=self.data_key, bucket_name=self.bucket_name,
                backend=self.backend
            )

            version = result[0]['version_id']

            # now test the download function
            url = '/download/sql/version/{}/'.format(version)
            request = self.factory.get(url, follow=True)
            request.user = self.user

            response = views.download_backup(request, backup_type='data',
                                             version_id=version)
            self.assertEqual(response.status_code, 200)
