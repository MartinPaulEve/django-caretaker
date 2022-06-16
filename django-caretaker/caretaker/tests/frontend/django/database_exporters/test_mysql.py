import tempfile
from pathlib import Path

import django
from django.core.management import CommandError
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper
from django.utils.connection import ConnectionDoesNotExist
from moto import mock_s3

from caretaker.frontend.frontends.database_exporters. \
    abstract_database_exporter import AbstractDatabaseExporter, \
    DatabaseExporterNotFoundError
from caretaker.frontend.frontends.database_exporters. \
    django.mysql import MysqlDatabaseExporter
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test
from caretaker.tests.utils import captured_output


@mock_s3
class TestMysqlDatabaseExporter(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for MysqlDatabaseExporter')

        self.create_bucket()

        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for MysqlDatabaseExporter')
        pass

    def test(self):
        self.logger.info('Testing MysqlDatabaseExporter')
        
        test_string = 'MySQL dump'
        database: str = 'mysql'

        with captured_output() as (stdout, stderr):
            self.frontend.export_sql(database=database)
            self.assertIn(test_string, stdout.getvalue())

        # check when we get no database
        with self.assertRaises(ConnectionDoesNotExist):
            self.frontend.export_sql('NON-EXISTENT DATABASE')

        # check when we get a database that we can't understand
        with self.assertRaises(DatabaseExporterNotFoundError):
            connection: BaseDatabaseWrapper | AbstractDatabaseExporter \
                = connections[database]
            connection.settings_dict['ENGINE'] = 'NON-EXISTENT DATABASE'
            self.frontend.export_sql(database=database)

        # switch it back and test for a failed binary call
        with self.assertRaises(CommandError):
            connection.settings_dict['ENGINE'] = 'django.db.backends.mysql'
            self.frontend.export_sql(alternative_binary='sqlite2000')

        # now test with bad args
        with self.assertRaises(CommandError):
            connection.settings_dict['ENGINE'] = 'django.db.backends.mysql'
            self.frontend.export_sql(alternative_args='JUNK_COMMAND')

        # test downloading to a file
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            output_file = 'test.sql'
            output_filename = Path(temporary_directory_name) / output_file

            self.frontend.export_sql(output_file=str(output_filename),
                                     database=database)

            self.assertTrue(output_filename.exists())

            with output_filename.open('r') as in_file:
                output = in_file.read()
                self.assertIn(test_string, output)

        # test property works
        exporter = MysqlDatabaseExporter()
        self.assertEqual(exporter.database_exporter_name, 'MySQL')

        exporter.binary_file = 'new_binary'
        self.assertEqual(exporter.binary_file, 'new_binary')

        return
