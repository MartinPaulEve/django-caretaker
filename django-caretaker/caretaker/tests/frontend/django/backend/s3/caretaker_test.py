import abc
import logging

import boto3

from django.conf import settings
from caretaker.backend.abstract_backend import BackendFactory
from caretaker.frontend.abstract_frontend import FrontendFactory
from caretaker.tests.caretaker_main_test import AbstractCaretakerTest
from caretaker.utils import log


class AbstractDjangoS3Test(AbstractCaretakerTest, metaclass=abc.ABCMeta):

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

        self.backend = BackendFactory.get_backend('Amazon S3')
        self.frontend = FrontendFactory.get_frontend('Django')

        self.json_key = 'test.json'
        self.dump_key = 'data.json'
        self.data_key = 'media.zip'
        self.test_contents = 'test'

        self.logger = log.get_logger('caretaker')

    def create_bucket(self):
        """
        Sets up a test bucket for a Django frontend, S3 backend scenario

        :return: None
        """
        self.backend.s3 = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id='fake_access_key',
            aws_secret_access_key='fake_secret_key',
        )

        self.bucket_name = 'a_test_bucket'
        self.backend.s3.create_bucket(Bucket=self.bucket_name)

        self.backend.s3.put_bucket_versioning(
            Bucket=self.bucket_name,
            ChecksumAlgorithm='CRC32',
            VersioningConfiguration={
                'Status': 'Enabled'
            }
        )
