from unittest.mock import patch

import django
from django.conf import settings
from moto import mock_s3

from caretaker.management.commands import export_sql
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test


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

        result = export_sql.command.callback(database='',
                                             frontend_name='Django')

        self.assertIn('COMMIT', result)

        with self.assertLogs(level='ERROR') as log:
            export_sql.command.callback(database='',
                                        frontend_name='NON')
            self.assertIn('Unable to find a valid frontend',
                          ''.join(log.output))
