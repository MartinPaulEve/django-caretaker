import tempfile
from pathlib import Path

from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test
from moto import mock_s3


@mock_s3
class TestTerraformOutputDjangoS3(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for Terraform test')

        self.create_bucket()

    def tearDown(self):
        self.logger.info('Teardown Terraform test')
        pass

    def test(self):
        self.logger.info('Running Terraform test')
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            self.frontend.generate_terraform(
                output_directory=temporary_directory_name,
                backend=self.backend
            )

            self.assertTrue(
                (Path(temporary_directory_name) / 'main.tf').exists())
            self.assertTrue(
                (Path(temporary_directory_name) / 'output.tf').exists())
