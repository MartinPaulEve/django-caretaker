import tempfile

from moto import mock_s3

from caretaker.tests.frontend.django.backend.local.caretaker_test import \
    AbstractDjangoLocalTest


@mock_s3
class TestTerraformOutputDjangoLocal(AbstractDjangoLocalTest):
    def setUp(self):
        self.logger.info('Setup for Terraform test')

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

            module = self.backend.terraform_template_module
