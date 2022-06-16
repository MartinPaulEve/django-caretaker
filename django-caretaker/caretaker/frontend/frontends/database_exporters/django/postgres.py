import logging

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.client import BaseDatabaseClient
from django.db.backends.postgresql.client import DatabaseClient

from caretaker.frontend.frontends import utils as frontend_utils
from caretaker.frontend.frontends.database_exporters. \
    abstract_database_exporter import AbstractDatabaseExporter
from caretaker.frontend.frontends.utils import DatabasePatcher
from caretaker.utils import log


class PostgresDatabaseExporter(AbstractDatabaseExporter):
    """
    The SQLite database exporters
    """

    _binary_name = 'pg_dump'

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

        self.logger = log.get_logger('caretaker-django-postgres-exporter')

    @property
    def database_exporter_name(self) -> str:
        """
        The display name of the database exporter

        :return: a string of the exporter name
        """
        return 'Postgresql'

    @property
    def handles(self) -> str:
        """
        The database engine that this class handles

        :return: a string of the database name (e.g. django.db.backends.sqlite3)
        """
        return 'django.db.backends.postgresql'

    def alternative_args(self, alternative_args: list | None) -> str:
        """
        A method that substitutes in alternative arguments to any called process

        :param alternative_args: the alternative arguments to use
        :return: a string of arguments
        """
        return str(frontend_utils.ternary_switch('', alternative_args))

    def client_type(self, connection: BaseDatabaseWrapper) \
            -> BaseDatabaseClient:
        """
        The type of client object to which to delegate command construction

        :param connection: the BaseDatabaseWrapper calling this
        :return: a BaseDatabaseClient
        """
        return DatabaseClient(connection=connection)

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
