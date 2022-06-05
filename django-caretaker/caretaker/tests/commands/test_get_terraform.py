import tempfile
from pathlib import Path

from django.test import TestCase
from moto import mock_s3

from get_terraform import Command as TerraformCommand
from tests.utils import setup_bucket


@mock_s3
class TestTerraformOutput(TestCase):
    def setUp(self):
        setup_bucket(self)

        self.logger.info('Setup for Terraform test')

        self.command = TerraformCommand()

    def tearDown(self):
        self.logger.info('Teardown Terraform test')
        pass

    def test_terraform(self):
        self.logger.info('Running Terraform test')
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            self.command._generate_terraform(
                output_directory=temporary_directory_name)

            self.assertTrue(
                (Path(temporary_directory_name) / 'main.tf').exists())
            self.assertTrue(
                (Path(temporary_directory_name) / 'output.tf').exists())
