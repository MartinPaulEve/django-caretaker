import tempfile
from logging import Logger
from pathlib import Path
from unittest.mock import patch

import django
from django.contrib.auth.models import User
from django.test import TestCase
from moto import mock_s3

from caretaker.utils import log
from caretaker.frontend.abstract_frontend import FrontendFactory, \
    AbstractFrontend, FrontendError


@mock_s3
class TestImportUnknownDjango(TestCase):
    def setUp(self):
        self.logger: Logger = log.get_logger('import-unknown-test')
        self.logger.info('Setup for test unknown import into Django')
        self.frontend: AbstractFrontend = FrontendFactory.get_frontend('Django')
        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for test unknown import into Django')
        pass

    def test(self):
        self.logger.info('Testing test unknown import into Django')

        # dump a JSON backup into the temporary directory
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            filename: str = 'data.json'
            file_path: Path = Path(temporary_directory_name) / filename

            with file_path.open('w') as out_file:
                out_file.write('SQL')

            with patch.object(Path, 'open') as mock_file:
                mock_file.side_effect = OSError

                # now do the restore
                with self.assertLogs(level='ERROR') as log:
                    self.frontend.import_file(
                        database='', input_file=str(file_path),
                        raise_on_error=False, dry_run=False
                    )

                    self.assertIn('Unable to determine',
                                  ''.join(log.output))

                # now test that it throws an error
                with self.assertRaises(FrontendError):
                    self.frontend.import_file(
                        database='', input_file=str(file_path),
                        raise_on_error=True, dry_run=False
                    )
