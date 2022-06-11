import django
from moto import mock_s3

import settings
from caretaker.backend.abstract_backend import BackendFactory, \
    BackendNotFoundError
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

    def _test_backend(self):
        backend = BackendFactory.get_backend('Amazon S3')
        self.assertIsNotNone(backend)

        # test that a non-existent backend doesn't load
        with self.assertRaises(BackendNotFoundError):
            BackendFactory.get_backend('Amazon S2', raise_on_none=True)

        # test that without the raise the backend loader returns None
        backend = BackendFactory.get_backend('Amazon S2')
        self.assertIsNone(backend)
