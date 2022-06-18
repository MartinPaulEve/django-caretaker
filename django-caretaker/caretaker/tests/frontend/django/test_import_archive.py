import shutil
import tempfile
from logging import Logger
from pathlib import Path

import django
from django.conf import settings
from django.test import TestCase
from moto import mock_s3

from caretaker.frontend.abstract_frontend import FrontendFactory, \
    AbstractFrontend
from caretaker.utils import log


@mock_s3
class TestImportJSONDjango(TestCase):
    def setUp(self):
        self.logger: Logger = log.get_logger('import-json-test')
        self.logger.info('Setup for test archive import into Django')
        self.frontend: AbstractFrontend = FrontendFactory.get_frontend('Django')
        django.setup()

        settings.CARETAKER_ADDITIONAL_BACKUP_PATHS = []
        settings.MEDIA_ROOT = ''

    def tearDown(self):
        self.logger.info('Teardown for test archive import into Django')
        pass

    def test(self):
        self.logger.info('Testing test archive import into Django')

        # make a temporary directory with some files in it
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            filename: str = 'my_test_file.txt'
            file_path: Path = Path(temporary_directory_name) / filename
            test_content = 'This is some test content'

            with file_path.open('w') as out_file:
                out_file.write(test_content)

            with tempfile.TemporaryDirectory() as backup_directory:
                self.frontend.create_backup(
                    output_directory=backup_directory,
                    path_list=[temporary_directory_name]
                )

                zip_file = Path(backup_directory) / 'media.zip'

                self.assertTrue(zip_file.exists())

                shutil.copy(zip_file, '/home/martin/new_media.zip')

                # unlink the dummy file in the test directory that we
                # want to test on restore
                self.logger.info('Unlinking {}'.format(file_path))
                file_path.unlink()
                self.assertFalse(file_path.exists())

                # test that a dry run doesn't really restore
                # now do the restore with dry run, which should fail
                self.frontend.import_file(
                    database='', input_file=str(zip_file),
                    raise_on_error=False, dry_run=True
                )
                self.assertFalse(file_path.exists())

                # now try a real restore
                self.frontend.import_file(
                    database='', input_file=str(zip_file),
                    raise_on_error=False, dry_run=False
                )
                self.assertTrue(file_path.exists())

                # now try deleting the whole directory and restoring
                shutil.rmtree(temporary_directory_name)

                self.assertFalse(file_path.exists())

                # test that a dry run doesn't really restore
                # now do the restore with dry run, which should fail
                self.frontend.import_file(
                    database='', input_file=str(zip_file),
                    raise_on_error=False, dry_run=True
                )
                self.assertFalse(file_path.exists())

                self.assertFalse(file_path.exists())
                self.frontend.import_file(
                    database='', input_file=str(zip_file),
                    raise_on_error=False, dry_run=False
                )
                self.assertTrue(file_path.exists())
