import tempfile
from pathlib import Path

import django
from moto import mock_s3

from caretaker.management.commands import export_sql
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test
from caretaker.tests.utils import captured_output


@mock_s3
class TestExportSQLCommand(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for export SQL command test')

        self.create_bucket()

        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for export SQL command test')
        pass

    def test(self):
        self.logger.info('Testing export SQL command test')

        with captured_output() as (stdout, stderr):
            export_sql.command.callback(database='',
                                        frontend_name='Django')

            self.assertIn('COMMIT', stdout.getvalue())

        # test downloading to a file
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            output_file = 'test.sql'
            output_filename = Path(temporary_directory_name) / output_file

            export_sql.command.callback(database='',
                                        frontend_name='Django',
                                        output_file=str(output_filename)
                                        )

            self.assertTrue(output_filename.exists())

            with output_filename.open('r') as in_file:
                output = in_file.read()
                self.assertIn('COMMIT', output)

        # test a permission we can't write to
        with self.assertLogs(level='ERROR') as log:
            export_sql.command.callback(database='',
                                        frontend_name='Django',
                                        output_file='/hsdfjl'
                                        )
            self.assertIn('Unable to open',
                          ''.join(log.output))

        with self.assertLogs(level='ERROR') as log:
            export_sql.command.callback(database='',
                                        frontend_name='NON')
            self.assertIn('Unable to find a valid frontend',
                          ''.join(log.output))
