import tempfile
from logging import Logger
from pathlib import Path

import django
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.test import TransactionTestCase

from caretaker.frontend.abstract_frontend import FrontendFactory, \
    AbstractFrontend
from caretaker.utils import log


class TestImportSQLDjango(TransactionTestCase):
    def setUp(self):
        self.logger: Logger = log.get_logger('import-sql-test')
        self.logger.info('Setup for test SQL import into Django')
        self.frontend: AbstractFrontend = FrontendFactory.get_frontend('Django')
        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for test SQL import into Django')
        pass

    def test(self):
        self.logger.info('Testing test SQL import into Django')

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

            self.frontend.reload_database(database='')

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
