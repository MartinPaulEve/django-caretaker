from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.client import BaseDatabaseClient
from django.db.backends.postgresql.client import DatabaseClient

from caretaker.frontend.frontends.database_importers. \
    abstract_database_importer import AbstractDatabaseImporter


class PostgresDatabaseImporter(AbstractDatabaseImporter):
    """
    The Postgres database importer
    """

    def _pre_hook(self, connection: BaseDatabaseWrapper,
                  input_file: str, sql_file: str,
                  rollback_directory: str) -> None:
        """
        A pre-hook function to allow individual importers to act

        :param connection: the connection object
        :param input_file: the input filename of the database (.sqlite)
        :param sql_file: the sql file to process (.sql)
        :param rollback_directory: a temporary directory to store rollbacks
        :return: None
        """
        pass

    def _rollback_hook(self, connection: BaseDatabaseWrapper,
                       input_file: str, sql_file: str,
                       rollback_directory: str) -> None:
        """
        A rollback hook to recover the database if possible

        :param connection: the connection object
        :param input_file: the input filename of the database (.sqlite3)
        :param sql_file: the SQL file to process (.sql)
        :param rollback_directory: a temporary directory to store rollbacks
        :return: None
        """
        # sorry, but by this point in postgres there's no easy rollback
        pass

    _binary_name = 'psql'
    _args = '-f'

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
        return 'Postgres'

    @property
    def handles(self) -> str:
        """
        The database engine that this class handles

        :return: a string of the database name (e.g. django.db.backends.sqlite3)
        """
        return 'django.db.backends.postgresql'

    def client_type(self, connection: BaseDatabaseWrapper) \
            -> BaseDatabaseClient:
        """
        The type of client object to which to delegate command construction

        :param connection: the BaseDatabaseWrapper calling this
        :return: a BaseDatabaseClient
        """
        return DatabaseClient(connection=connection)
