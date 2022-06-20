import tempfile
from pathlib import Path

from caretaker.backend.abstract_backend import BackendNotFoundError
from caretaker.frontend.abstract_frontend import FrontendNotFoundError
from caretaker.management.commands import get_terraform
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test
from moto import mock_s3


@mock_s3
class TestTerraformOutputDjangoS3Command(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for Terraform command test')

        self.create_bucket()

    def tearDown(self):
        self.logger.info('Teardown Terraform command test')
        pass

    def test(self):
        self.logger.info('Running Terraform command test')
        with tempfile.TemporaryDirectory() as temporary_directory_name:

            get_terraform.command.callback(
                output_directory=temporary_directory_name,
                backend_name=self.backend.backend_name,
                frontend_name=self.frontend.frontend_name
            )

            self.assertTrue(
                (Path(temporary_directory_name) / 'main.tf').exists())
            self.assertTrue(
                (Path(temporary_directory_name) / 'output.tf').exists())

            with self.assertLogs(level='ERROR') as log:
                get_terraform.command.callback(
                    output_directory=temporary_directory_name,
                    backend_name='NON',
                    frontend_name=self.frontend.frontend_name
                    )
                self.assertIn('Unable to find a valid backend',
                              ''.join(log.output))

            with self.assertLogs(level='ERROR') as log:
                get_terraform.command.callback(
                    output_directory=temporary_directory_name,
                    backend_name=self.backend.backend_name,
                    frontend_name='NON'
                )
                self.assertIn('Unable to find a valid frontend',
                              ''.join(log.output))
