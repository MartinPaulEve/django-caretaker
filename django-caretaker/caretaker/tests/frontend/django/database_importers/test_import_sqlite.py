import tempfile
from logging import Logger
from pathlib import Path

import django
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.backends.base.base import BaseDatabaseWrapper
from django.test import TransactionTestCase
from django.utils.connection import ConnectionDoesNotExist

from caretaker.frontend.abstract_frontend import FrontendFactory, \
    AbstractFrontend
from caretaker.frontend.frontends.database_importers. \
    abstract_database_importer import DatabaseImporterNotFoundError, \
    AbstractDatabaseImporter
from caretaker.frontend.frontends.database_importers. \
    django.sqlite import SQLiteDatabaseImporter
from caretaker.utils import log


class TestImportSQLDjango(TransactionTestCase):
    def setUp(self):
        self.logger: Logger = log.get_logger('import-sqlite-test')
        self.logger.info('Setup for test SQLlite import into Django')
        self.frontend: AbstractFrontend = FrontendFactory.get_frontend('Django')
        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for test SQLlite import into Django')
        pass

    def test(self):
        self.logger.info('Testing test SQLlite import into Django')

        # first, insert something into the database
        username: str = 'test_user'
        User.objects.create_user(username=username, email='martin@eve.gd',
                                 password='test_password_123')

        # now re-fetch the user
        user: User = User.objects.get(username=username)
        self.assertEqual(user.username, username)

        # dump a JSON backup into the temporary directory
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            filename: str = 'data.sql'
            file_path: Path = Path(temporary_directory_name) / filename

            self.frontend.export_sql(output_file=str(file_path))

            self.assertTrue(file_path.exists())

            # now modify the database
            second_username: str = 'user2'
            user.username = second_username
            user.save()

            # assert we can't find it with the original username
            with self.assertRaises(ObjectDoesNotExist):
                User.objects.get(username=username)

            # now do the restore with dry run, which should fail
            self.frontend.import_file(
                database='', input_file=str(file_path),
                raise_on_error=False, dry_run=True
            )

            with self.assertRaises(ObjectDoesNotExist):
                User.objects.get(username=username)

            # now do the real restore with dry run, which should fail
            self.frontend.import_file(
                database='', input_file=str(file_path),
                raise_on_error=False, dry_run=False
            )

            # now this should not raise an error
            user: User = User.objects.get(username=username)
            self.assertEqual(user.username, username)

            # try to import a file that doesn't exist
            with self.assertLogs(level='ERROR') as log_file:
                self.frontend.import_file(
                    database='', input_file='/junk',
                    raise_on_error=False, dry_run=False
                )

                self.assertIn('does not exist',
                              ''.join(log_file.output))

            # now check that it throws an exception
            with self.assertRaises(FileNotFoundError):
                self.frontend.import_file(
                    database='', input_file='/junk',
                    raise_on_error=True, dry_run=False
                )

            # check when we get no database
            with self.assertRaises(ConnectionDoesNotExist):
                self.frontend.import_file(database='NON-EXISTENT DATABASE',
                                          input_file=str(file_path),
                                          raise_on_error=True, dry_run=True)

            # check when we get a database that we can't understand
            with self.assertRaises(DatabaseImporterNotFoundError):
                database: str = DEFAULT_DB_ALIAS
                connection: BaseDatabaseWrapper | AbstractDatabaseImporter \
                    = connections[database]
                connection.settings_dict['ENGINE'] = 'NON-EXISTENT DATABASE'
                self.frontend.import_file(input_file=str(file_path),
                                          raise_on_error=True, dry_run=True)

            # switch it back and test for a failed binary call
            with self.assertRaises(CommandError):
                connection.settings_dict['ENGINE'] = \
                    'django.db.backends.sqlite3'
                self.frontend.import_file(input_file=str(file_path),
                                          raise_on_error=True, dry_run=False,
                                          alternative_binary='sqlite2000')

            # now test with bad args
            with self.assertRaises(CommandError):
                connection.settings_dict['ENGINE'] = \
                    'django.db.backends.sqlite3'
                self.frontend.import_file(input_file=str(file_path),
                                          raise_on_error=True, dry_run=False,
                                          alternative_args=['JUNK_COMMAND'])

            # test property works
            importer = SQLiteDatabaseImporter()
            self.assertEqual(importer.database_importer_name, 'SQLite')

            importer.binary_file = 'new_binary'
            self.assertEqual(importer.binary_file, 'new_binary')
