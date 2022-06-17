import abc
import shutil
import subprocess
import sys
from logging import Logger
from pathlib import Path
from typing import TextIO
from typing.io import BinaryIO

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.client import BaseDatabaseClient

from caretaker.frontend.frontends import utils as frontend_utils
from caretaker.frontend.frontends.database_exporters.django import utils
from caretaker.frontend.frontends.utils import BufferedProcessReader, \
    DatabasePatcher
from caretaker.utils import log


class AbstractDatabaseImporter(metaclass=abc.ABCMeta):
    """
    Ab abstract class for data importers
    """

    _args = ''

    def __init__(self):
        """
        Instantiate a database importer

        """
        self.logger: Logger = log.get_logger(
            '{}-importer'.format(self.database_importer_name))

    @property
    @abc.abstractmethod
    def database_importer_name(self) -> str:
        """
        The display name of the database importer

        :return: a string of the importer name
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

    @property
    def provided_args(self) -> str:
        """
        The arguments provided by this implementation

        :return: a string of arguments
        """

        return self._args

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
            alternative_args=str(
                frontend_utils.ternary_switch(self.provided_args,
                                              alternative_args)),
            binary_name=self._binary_final(alternative_binary),
            settings_dict=connection.settings_dict,
            database_client=self.client_type(connection)
        )

    @abc.abstractmethod
    def _pre_hook(self, connection: BaseDatabaseWrapper,
                  input_file: str, sql_file: str) -> None:
        """
        A pre-hook function to allow individual importers to act

        :param connection: the connection object
        :param input_file: the input filename of the SQL
        :param sql_file: the sql file to process
        :return: None
        """
        pass

    def import_sql(self, connection: BaseDatabaseWrapper, input_file: str,
                   alternative_binary: str = '',
                   alternative_args: list | None = None) -> TextIO | BinaryIO:
        """
        Export SQL from the database using the specific provider

        :param connection: the connection object
        :param alternative_binary: the alternative binary to use
        :param alternative_args: a different set of cmdline args to pass
        :param input_file: the input filename of the SQL
        :return: a string of the database to output
        """
        logger = log.get_logger('sql-importer')

        self._pre_hook(connection=connection,
                       input_file=str(connection.settings_dict['NAME']),
                       sql_file=input_file)

        if self._args != '':
            self._args = '{} {}'.format(self._args, input_file)

        args, env = self.args_and_env(
            connection=connection, alternative_binary=alternative_binary,
            alternative_args=alternative_args
        )

        # convert to str in case a PosixPath switch has happened
        final_args = [str(arg) for arg in args]

        logger.info('Running: {}'.format(' '.join(final_args)))
        process: subprocess.Popen = subprocess.Popen(final_args,
                                                     env=env,
                                                     stdout=subprocess.PIPE,
                                                     bufsize=8192, shell=False)

        reader = BufferedProcessReader(process)
        reader.handle_process(output_filename='-')

        if process.returncode != 0:
            raise subprocess.CalledProcessError(returncode=process.returncode,
                                                cmd=' '.join(args),
                                                output='Output not available')

        # verify if the file now exists
        print('Does {} exist?'.format(connection.settings_dict['NAME']))
        print(Path(connection.settings_dict['NAME']).exists())

        return sys.stdout

    def patch(self, connection: BaseDatabaseWrapper) -> bool:
        """
        Patches the connection object with a method "export_sql" or removes this method if it's already set to this function's setting

        :param connection: the connection object
        :return: boolean of whether the object was patched
        """
        # determine if we can handle this
        if DatabasePatcher.can_handle(connection, self):
            connection.import_sql = self.import_sql
            return True

        return False


class DatabaseImporterNotFoundError (Exception):
    """
    Occurs when a database exporter cannot be found to handle the current engine
    """
    pass
