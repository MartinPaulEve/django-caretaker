import sys
import zipfile
from contextlib import contextmanager
from io import StringIO
from pathlib import Path

import botocore.exceptions

from caretaker.backend.abstract_backend import StoreOutcome
from caretaker.tests.caretaker_main_test import AbstractCaretakerTest
from caretaker.utils import file


def upload_temporary_file(test_class: AbstractCaretakerTest,
                          temporary_directory_name: str,
                          contents: str,
                          check_identical: bool = True,
                          remote_key: str = '',
                          commit: bool = True) \
        -> (StoreOutcome, Path):
    """
    Create a temporary file and upload it to the mocked backend

    :param test_class: the test case in question
    :param temporary_directory_name: the output directory to use
    :param contents: the contents to write to the file
    :param check_identical: check whether the file exists in the remote store
    :param remote_key: the remote key (filename) to store
    :param commit: whether to push the file to the remote store
    :return: a 2-tuple of StoreOutcome and pathlib.Path to the file
    """

    remote_key = remote_key if remote_key else test_class.json_key

    temporary_file = file.normalize_path(
        temporary_directory_name) / remote_key

    with temporary_file.open('w') as out_file:
        out_file.write(contents)

    # run the first time to store the result
    if commit:
        result = test_class.frontend.push_backup(
            backup_local_file=temporary_file, remote_key=remote_key,
            backend=test_class.backend, bucket_name=test_class.bucket_name,
            check_identical=check_identical)
    else:
        result = StoreOutcome.FAILED

    return result, temporary_file


def file_in_zip(zip_file: str, filename: str) -> bool:
    """
    Test whether a file exists inside a zip

    :param zip_file: the input zip file
    :param filename: the file to check for
    :return: True if found, else False
    """
    zip_file = file.normalize_path(zip_file)

    with zipfile.ZipFile(zip_file, 'r') as zf:
        name_list = [filename.split('/')[-1]
                     for filename in zf.namelist()]
        return filename in name_list


def boto3_error(operation_name: str) -> botocore.exceptions.ClientError:
    sub_error = {'Code': '123', 'Message': 'A Message'}
    error = {'Error': sub_error}
    return botocore.exceptions.ClientError(operation_name=operation_name,
                                           error_response=error)


@contextmanager
def captured_output():
    """
    Capture the value of stdout and stderr for testing

    :return: stdout and stderr
    """
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err
