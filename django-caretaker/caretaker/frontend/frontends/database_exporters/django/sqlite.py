import logging
import logging
import os
import subprocess
import sys
from typing import TextIO
from typing.io import BinaryIO

from django.db.backends.base.base import BaseDatabaseWrapper

from caretaker.frontend.frontends.database_exporters. \
    abstract_database_exporter import AbstractDatabaseExporter
from caretaker.frontend.frontends.utils import DatabasePatcher, \
    BufferedProcessReader
from caretaker.utils import log


class SQLiteDatabaseExporter(AbstractDatabaseExporter):
    """
    The SQLite database exporters
    """

    _binary_name = 'sqlite3'

    @property
    def binary_file(self) -> str:
        """
        The binary file to execute

        :return: a path to a binary executable
        """
        return self._binary_name

    @binary_file.setter
    def binary_file(self, value):
        """
        Set the binary file to execute

        :param: value: the binary executable
        """
        self._binary_name = value

    def __init__(self, logger: logging.Logger | None = None):
        super().__init__(logger)

        self.logger = log.get_logger('caretaker-django-sqlite-exporter')

    @property
    def database_exporter_name(self) -> str:
        """
        The display name of the database exporter

        :return: a string of the exporter name
        """
        return 'SQLite'

    @property
    def handles(self) -> str:
        """
        The database engine that this class handles

        :return: a string of the database name (e.g. django.db.backends.sqlite3)
        """
        return 'django.db.backends.sqlite3'

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
        binary_name = self._binary_name \
            if not alternative_binary else alternative_binary

        args = [binary_name, connection.settings_dict["NAME"],
                '.dump' if not alternative_args else alternative_args]
        env = None
        env = {**os.environ, **env} if env else None

        process: subprocess.Popen = subprocess.Popen(args,
                                                     env=env,
                                                     stdout=subprocess.PIPE,
                                                     bufsize=8192, shell=False)

        reader = BufferedProcessReader(process)
        reader.handle_process(output_filename=output_file)

        if process.returncode != 0:
            raise subprocess.CalledProcessError(returncode=process.returncode,
                                                cmd=''.join(args),
                                                output='Output not available')

        return sys.stdout

    def patch(self, connection: BaseDatabaseWrapper) -> bool:
        """
        Patches the connection object with a method "export_sql" or removes this method if it's already set to this function's setting

        :param connection: the connection object
        :return: boolean of whether the object was patched
        """
        # determine if we can handle this
        if DatabasePatcher.can_handle(connection, self):
            connection.export_sql = self.export_sql
            return True

        return False
