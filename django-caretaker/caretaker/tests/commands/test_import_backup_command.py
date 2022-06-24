import tempfile
from logging import Logger
from pathlib import Path
from unittest.mock import patch

import django
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.test import TransactionTestCase

from caretaker.frontend.abstract_frontend import FrontendFactory, \
    AbstractFrontend
from caretaker.management.commands import import_backup
from caretaker.utils import log


class TestImportSQLiteDjango(TransactionTestCase):
    def setUp(self):
        self.logger: Logger = log.get_logger('import-sqlite-test')
        self.logger.info('Setup for test SQLlite import command')
        self.frontend: AbstractFrontend = FrontendFactory.get_frontend('Django')
        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for test SQLlite import command')
        pass

    def test(self):
        self.logger.info('Testing test SQLlite import command')

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
            import_backup.command.callback(
                input_file=file_path,
                dry_run=True,
                frontend_name=self.frontend.frontend_name
            )

            with self.assertRaises(ObjectDoesNotExist):
                User.objects.get(username=username)

            # now do the real restore with dry run, which should fail
            import_backup.command.callback(
                input_file=file_path,
                dry_run=False,
                frontend_name=self.frontend.frontend_name
            )

            # now this should not raise an error
            user: User = User.objects.get(username=username)
            self.assertEqual(user.username, username)

            # now test for loaders failing
            with self.assertLogs(level='ERROR') as log_obj:
                import_backup.command.callback(
                    input_file=file_path,
                    dry_run=False,
                    frontend_name='NON'
                )
                self.assertIn('Unable to find a valid frontend',
                              ''.join(log_obj.output))

            # patch for error handling
            with patch(
                    'caretaker.frontend.abstract_frontend.FrontendFactory.'
                    'get_frontend',
                    side_effect=PermissionError('Oh dear how sad never mind')):
                with self.assertLogs(level='ERROR') as log_obj:
                    import_backup.command.callback(
                        input_file=file_path,
                        dry_run=False,
                        frontend_name='NON'
                    )
                    self.assertIn('Unable to open output file',
                                  ''.join(log_obj.output))
