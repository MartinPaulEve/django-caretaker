import sqlite3
from pathlib import Path

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.client import BaseDatabaseClient
from django.db.backends.sqlite3.client import DatabaseClient

from caretaker.frontend.frontends.database_importers.\
    abstract_database_importer import AbstractDatabaseImporter


class SQLiteDatabaseImporter(AbstractDatabaseImporter):
    """
    The SQLite database exporters
    """

    def _pre_hook(self, connection: BaseDatabaseWrapper,
                  input_file: str, sql_file: str) -> None:

        if not input_file.startswith('file:'):
            self.logger.info('Unlinking {} from the filesystem'.format(
                input_file))
            Path(input_file).unlink()

    _binary_name = 'sqlite3'
    _args = '.read'

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

    @property
    def database_importer_name(self) -> str:
        """
        The display name of the database importer

        :return: a string of the importer name
        """
        return 'SQLite'

    @property
    def handles(self) -> str:
        """
        The database engine that this class handles

        :return: a string of the database name (e.g. django.db.backends.sqlite3)
        """
        return 'django.db.backends.sqlite3'

    def client_type(self, connection: BaseDatabaseWrapper) \
            -> BaseDatabaseClient:
        """
        The type of client object to which to delegate command construction

        :param connection: the BaseDatabaseWrapper calling this
        :return: a BaseDatabaseClient
        """
        return DatabaseClient(connection=connection)
