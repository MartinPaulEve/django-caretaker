import abc
import logging
import subprocess
import sys
from typing import TextIO
from typing.io import BinaryIO

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.client import BaseDatabaseClient

from caretaker.frontend.frontends.utils import BufferedProcessReader
from caretaker.frontend.frontends.database_exporters.django import utils
from caretaker.frontend.frontends import utils as frontend_utils


class AbstractDatabaseExporter(metaclass=abc.ABCMeta):
    """
    Ab abstract class for data exporters
    """

    @abc.abstractmethod
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger

    @property
    @abc.abstractmethod
    def database_exporter_name(self) -> str:
        """
        The display name of the database exporter

        :return: a string of the exporter name
        """
        pass

    @property
    @abc.abstractmethod
    def binary_file(self) -> str:
        """
        The binary file to execute

        :return: a path to a binary executable
        """
        pass

    @property
    @abc.abstractmethod
    def handles(self) -> str:
        """
        The database engine that this class handles

        :return: a string of the database name (e.g. django.db.backends.sqlite3)
        """
        pass

    def _binary_final(self, alternative_binary: str) -> str:
        """
        The final binary to use, allowing a provider to change this if necessary

        :param alternative_binary:
        :return: the final binary
        """
        return str(frontend_utils.ternary_switch(self.binary_file,
                                                 alternative_binary))

    @abc.abstractmethod
    def alternative_args(self, alternative_args: list | None) -> str:
        """
        A method that substitutes in alternative arguments to any called process

        :param alternative_args: the alternative arguments to use
        :return: a string of arguments
        """
        pass

    @abc.abstractmethod
    def client_type(self, connection: BaseDatabaseWrapper) \
            -> BaseDatabaseClient:
        """
        The type of client object to which to delegate command construction

        :param connection: the BaseDatabaseWrapper calling this
        :return: a BaseDatabaseClient
        """
        pass

    def args_and_env(self, connection: BaseDatabaseWrapper,
                     alternative_binary: str = '',
                     alternative_args: list | None = None) -> (list, dict):
        """
        Returns the parameters needed to export SQL for this provider

        :param connection: the connection object
        :param alternative_binary: the alternative binary to use
        :param alternative_args: a different set of cmdline args to pass
        :return: 2-tuple of array of arguments and dict of environment variables
        """
        return utils.delegate_settings_to_cmd_args(
            alternative_args=self.alternative_args(alternative_args),
            binary_name=self._binary_final(alternative_binary),
            settings_dict=connection.settings_dict,
            database_client=self.client_type(connection)
        )

    def export_sql(self, connection: BaseDatabaseWrapper,
                   alternative_binary: str = '',
                   alternative_args: list | None = None,
                   output_file: str = '-') -> TextIO | BinaryIO:
        """
        Export SQL from the database using the specific provider

        :param connection: the connection object
        :param alternative_binary: the alternative binary to use
        :param alternative_args: a different set of cmdline args to pass
        :param output_file: an output file to write to rather than stdout
        :return: a string of the database to output
        """
        args, env = self.args_and_env(
            connection=connection, alternative_binary=alternative_binary,
            alternative_args=alternative_args
        )

        process: subprocess.Popen = subprocess.Popen(args,
                                                     env=env,
                                                     stdout=subprocess.PIPE,
                                                     bufsize=8192, shell=False)

        reader = BufferedProcessReader(process)
        reader.handle_process(output_filename=output_file)

        if process.returncode != 0:
            raise subprocess.CalledProcessError(returncode=process.returncode,
                                                cmd=' '.join(args),
                                                output='Output not available')

        return sys.stdout if output_file == '-' else output_file

    @staticmethod
    @abc.abstractmethod
    def patch(connection: BaseDatabaseWrapper) -> bool:
        """
        Export SQL from the database using the specific provider

        :param connection: the connection object
        :return: boolean of whether the object was patched
        """
        pass


class DatabaseExporterNotFoundError (Exception):
    """
    Occurs when a database exporter cannot be found to handle the current engine
    """
    pass
