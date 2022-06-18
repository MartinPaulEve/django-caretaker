import tempfile
from logging import Logger
from pathlib import Path

import django
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.test import TransactionTestCase

from caretaker.frontend.abstract_frontend import FrontendFactory, \
    AbstractFrontend
from caretaker.frontend.frontends.database_importers. \
    django.mysql import MysqlDatabaseImporter
from caretaker.utils import log


class TestImportPostgresDjango(TransactionTestCase):
    databases = {'mysql'}

    def setUp(self):
        self.logger: Logger = log.get_logger('import-mysql-test')
        self.logger.info('Setup for test MySQL import into Django')
        self.frontend: AbstractFrontend = FrontendFactory.get_frontend('Django')
        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for test MySQL import into Django')
        pass

    def test(self):
        self.logger.info('Testing test MySQL import into Django')

        database_name = 'mysql'

        # first, insert something into the database
        username: str = 'test_user'
        User.objects.using(database_name).create(username=username,
                                                 email='martin@eve.gd',
                                                 password='test_password_123')

        # now re-fetch the user
        user: User = User.objects.using(database_name).get(username=username)
        self.assertEqual(user.username, username)

        # dump a JSON backup into the temporary directory
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            filename: str = 'data.sql'
            file_path: Path = Path(temporary_directory_name) / filename

            self.frontend.export_sql(output_file=str(file_path),
                                     database=database_name)

            self.assertTrue(file_path.exists())

            # now modify the database
            second_username: str = 'user2'
            user.username = second_username
            user.save()

            # assert we can't find it with the original username
            with self.assertRaises(ObjectDoesNotExist):
                User.objects.using(database_name).get(username=username)

            # now do the restore with dry run, which should fail
            self.frontend.import_file(
                database=database_name, input_file=str(file_path),
                raise_on_error=False, dry_run=True
            )

            with self.assertRaises(ObjectDoesNotExist):
                User.objects.using(database_name).get(username=username)

            # now do the real restore with dry run, which should fail
            self.frontend.import_file(
                database=database_name, input_file=str(file_path),
                raise_on_error=False, dry_run=False
            )

            # now this should not raise an error
            user: User = User.objects.using(database_name).get(
                username=username)
            self.assertEqual(user.username, username)

            # try to import a file that doesn't exist
            with self.assertLogs(level='ERROR') as log_file:
                self.frontend.import_file(
                    database=database_name, input_file='/junk',
                    raise_on_error=False, dry_run=False
                )

                self.assertIn('does not exist',
                              ''.join(log_file.output))

            # now check that it throws an exception
            with self.assertRaises(FileNotFoundError):
                self.frontend.import_file(
                    database=database_name, input_file='/junk',
                    raise_on_error=True, dry_run=False
                )

            # test property works
            importer = MysqlDatabaseImporter()
            self.assertEqual(importer.database_importer_name, 'MySQL')

            importer.binary_file = 'new_binary'
            self.assertEqual(importer.binary_file, 'new_binary')

            importer._rollback_hook(connection=None, sql_file='', input_file='',
                                    rollback_directory='')
