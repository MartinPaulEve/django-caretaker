import abc
import logging

import boto3

from django.conf import settings
from caretaker.backend.abstract_backend import BackendFactory
from caretaker.frontend.abstract_frontend import FrontendFactory
from caretaker.tests.caretaker_main_test import AbstractCaretakerTest
from caretaker.utils import log


class AbstractDjangoLocalTest(AbstractCaretakerTest, metaclass=abc.ABCMeta):

    json_key = 'test.json'
    dump_key = 'data.json'
    data_key = 'media.zip'
    test_contents = 'test'

    backend = None
    frontend = None

    def __init__(self, logger: logging.Logger | None = None):
        super().__init__(logger=logger, method_name='test')

        settings.CARETAKER_ADDITIONAL_BACKUP_PATHS = []
        settings.MEDIA_ROOT = ''
        settings.CARETAKER_BACKENDS = []
        settings.CARETAKER_FRONTENDS = []
        settings.CARETAKER_BACKEND = ''
        settings.CARETAKER_FRONTEND = ''
        settings.CARETAKER_BACKUP_BUCKET = 'caretaker_bucket'
        settings.CARETAKER_LOCAL_STORE_DIRECTORY = ''
        settings.CARETAKER_LOCAL_FILE_PATTERN = '{{version}}.{{date}}'

        self.bucket_name = settings.CARETAKER_BACKUP_BUCKET

        self.backend = BackendFactory.get_backend('Local')
        self.frontend = FrontendFactory.get_frontend('Django')

        self.json_key = 'test.json'
        self.dump_key = 'data.json'
        self.data_key = 'media.zip'
        self.test_contents = 'test'

        self.logger = log.get_logger('')
