import logging

from django.test import TestCase
import abc

from moto import mock_s3

from caretaker.utils import log


@mock_s3
class AbstractCaretakerTest(TestCase, metaclass=abc.ABCMeta):
    json_key = 'test.json'
    dump_key = 'data.json'
    data_key = 'media.zip'
    test_contents = 'test'
    bucket_name = ''

    logger = None
    backend = None
    frontend = None

    def __init__(self, logger: logging.Logger | None = None,
                 method_name='test'):
        super().__init__(methodName=method_name)
        self.logger = logger

        self.logger = log.get_logger('caretaker')
