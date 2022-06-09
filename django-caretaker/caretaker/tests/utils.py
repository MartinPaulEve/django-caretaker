import os
import zipfile
from pathlib import Path

import boto3
import django.test

from caretaker.backend.abstract_backend import BackendFactory, StoreOutcome
from caretaker.utils import log, file
from caretaker.management.commands.push_backup import Command as PushCommand

DEV_NULL = open(os.devnull, "w")


def setup_test_class_s3(test_class: django.test.TestCase) \
        -> django.test.TestCase:
    """
    Generic class to set up/mutate test objects
    :param test_class: the class to mutate
    :return: the mutated test class
    """
    test_class.command = PushCommand()
    test_class.json_key = 'test.json'
    test_class.dump_key = 'data.json'
    test_class.data_key = 'media.zip'
    test_class.test_contents = 'test'

    test_class.logger = log.get_logger('caretaker')

    test_class.client = boto3.client(
        's3',
        region_name='us-east-1',
        aws_access_key_id='fake_access_key',
        aws_secret_access_key='fake_secret_key',
    )

    test_class.bucket_name = 'a_test_bucket'
    test_class.client.create_bucket(Bucket=test_class.bucket_name)
    test_class.client.put_bucket_versioning(
        Bucket=test_class.bucket_name,
        ChecksumAlgorithm='CRC32',
        VersioningConfiguration={
            'Status': 'Enabled'
        }
    )

    test_class.backend = BackendFactory.get_backend('Amazon S3')

    return test_class


def upload_temporary_file(test_class: django.test.TestCase,
                          temporary_directory_name: str,
                          contents: str) -> (StoreOutcome, Path):
    """
    Create a temporary file and upload it to the mocked backend
    :param test_class: the test case in question
    :param temporary_directory_name: the output directory to use
    :param contents: the contents to write to the file
    :return: a 2-tuple of StoreOutcome and pathlib.Path to the file
    """

    temporary_file = file.normalize_path(
        temporary_directory_name) / test_class.json_key

    with temporary_file.open('w') as out_file:
        out_file.write(contents)

    # run the first time to store the result
    result = test_class.command.push_backup(
        backup_local_file=temporary_file, remote_key=test_class.json_key,
        backend=test_class.backend, bucket_name=test_class.bucket_name)

    return result, temporary_file


def file_in_zip(zip_file, filename):
    with zipfile.ZipFile(zip_file, 'r') as zf:
        name_list = [filename.split('/')[-1]
                     for filename in zf.namelist()]
        return filename in name_list
