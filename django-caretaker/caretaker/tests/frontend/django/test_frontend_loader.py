import django
from django.conf import settings
from moto import mock_s3

from caretaker.frontend.abstract_frontend import FrontendFactory, \
    AbstractFrontend, FrontendNotFoundError
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test


@mock_s3
class TestCreateFrontendDjango(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for frontend_loader_django')

        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for frontend_loader_django')
        pass

    def test(self):
        self.logger.info('Testing frontend_loader_django')

        # load a backend by name
        self._test_frontend()

        # test loading when there's nothing in settings
        settings.CARETAKER_FRONTEND = ''
        self._test_frontend()

        # now blank the CARETAKER_BACKENDS field
        settings.CARETAKER_FRONTENDS = []
        self._test_frontend()

        # test loading multiple backends
        settings.CARETAKER_FRONTENDS = [
            'caretaker.tests.frontend.mock_frontend',
            'caretaker.frontend.frontends.django'
        ]

        self._test_frontend()
        instance = FrontendFactory.get_frontend('Mock Frontend')
        self.assertIsNotNone(instance)
        self.assertEqual(instance.frontend_name, 'Mock Frontend')

        # test that we load from settings
        settings.CARETAKER_FRONTEND = 'Mock Frontend'
        self._test_frontend()
        instance = FrontendFactory.get_frontend('')
        self.assertIsNotNone(instance)
        self.assertEqual(instance.frontend_name, 'Mock Frontend')

    def _test_frontend(self) -> AbstractFrontend:
        """
        Test the backend functionality

        :return: an S3 backend
        """
        frontend_django = FrontendFactory.get_frontend('Django')
        self.assertIsNotNone(frontend_django)
        self.assertEqual(frontend_django.frontend_name, 'Django')

        # test default
        frontend = FrontendFactory.get_frontend('')
        self.assertIsNotNone(frontend)

        # test that a non-existent backend doesn't load
        with self.assertRaises(FrontendNotFoundError):
            FrontendFactory.get_frontend('DOES NOT EXIST', raise_on_none=True)

        # test that without the raise the backend loader returns None
        frontend = FrontendFactory.get_frontend('DOES NOT EXIST')
        self.assertIsNone(frontend)

        return frontend_django
