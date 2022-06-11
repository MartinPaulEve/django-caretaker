import abc
import logging
from pathlib import Path

import django.test

from caretaker.backend.abstract_backend import AbstractBackend

from unittest.mock import patch

from caretaker.tests.caretaker_main_test import AbstractCaretakerTest

from caretaker.utils import log


class AbstractBackendTest(AbstractCaretakerTest, metaclass=abc.ABCMeta):
    def __init__(self, logger: logging.Logger | None = None):
        super().__init__(logger=logger, method_name='test')

        self.logger = log.get_logger('caretaker')

    def setUp(self):
        self.logger.info('Setup for abstract backend test')

        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for abstract backend test')
        pass

    @patch.multiple(AbstractBackend, __abstractmethods__=set())
    def test(self) -> None:
        """
        This test exists solely to give full coverage to abstract backend

        :return: None
        """
        instance = AbstractBackend()

        # properties
        files = instance.terraform_files
        name = instance.backend_name
        module = instance.terraform_template_module

        instance.get_object(remote_key='', bucket_name='', version_id='')
        instance.versions(bucket_name='a_test', remote_key='data.json')
        instance.store_object(local_file=Path('~/'), bucket_name='',
                              remote_key='', check_identical=True)
        instance.download_object(version_id='', bucket_name='', remote_key='',
                                 local_file=Path('~/'))
