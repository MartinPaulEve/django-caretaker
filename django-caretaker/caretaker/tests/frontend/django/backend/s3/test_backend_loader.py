from pathlib import Path

import django
from moto import mock_s3

from django.conf import settings
from caretaker.backend.abstract_backend import BackendFactory, \
    BackendNotFoundError, AbstractBackend
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test


@mock_s3
class TestCreateBackupDjangoS3(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for backend_loader_s3')

        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for backup_loader_s3')
        pass

    def test(self):
        self.logger.info('Testing backup_loader_s3')

        # load a backend by name
        self._test_backend()

        # test loading when there's nothing in settings
        settings.CARETAKER_BACKEND = ''
        self._test_backend()

        # now blank the CARETAKER_BACKENDS field
        settings.CARETAKER_BACKENDS = []
        self._test_backend()

        # test loading multiple backends
        settings.CARETAKER_BACKENDS = [
            'caretaker.tests.frontend.django.backend.s3.mock_backend',
            'caretaker.backend.backends.s3']
        self._test_backend()
        instance = BackendFactory.get_backend('Mock S3')
        self.assertIsNotNone(instance)
        self.assertEqual(instance.backend_name, 'Mock S3')

        # call functions in this mocked entity for coverage
        files = instance.terraform_files
        module = instance.terraform_template_module

        instance.get_object(remote_key='', bucket_name='', version_id='')
        instance.versions(bucket_name='a_test', remote_key='data.json')
        instance.store_object(local_file=Path('~/'), bucket_name='',
                              remote_key='', check_identical=True)
        instance.download_object(version_id='', bucket_name='', remote_key='',
                                 local_file=Path('~/'))

    def _test_backend(self) -> AbstractBackend:
        """
        Test the backend functionality

        :return: an S3 backend
        """
        backend_s3 = BackendFactory.get_backend('Amazon S3')
        self.assertIsNotNone(backend_s3)
        self.assertEqual(backend_s3.backend_name, 'Amazon S3')

        # test default
        backend = BackendFactory.get_backend('')
        self.assertIsNotNone(backend)

        # test that a non-existent backend doesn't load
        with self.assertRaises(BackendNotFoundError):
            BackendFactory.get_backend('Amazon S2', raise_on_none=True)

        # test that without the raise the backend loader returns None
        backend = BackendFactory.get_backend('Amazon S2')
        self.assertIsNone(backend)

        return backend_s3
