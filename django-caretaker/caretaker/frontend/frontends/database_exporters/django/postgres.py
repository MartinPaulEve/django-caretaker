import logging

import django.db.backends.postgresql.client
from django.db.backends.base.base import BaseDatabaseWrapper

from caretaker.frontend.frontends.database_exporters. \
    abstract_database_exporter import AbstractDatabaseExporter
from caretaker.frontend.frontends.utils import DatabasePatcher
from caretaker.utils import log
from  django.db.backends.postgresql.client import DatabaseClient


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
        return 'django.db.backends.postgresql'

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
        binary_name = self._binary_name \
            if not alternative_binary else alternative_binary

        settings_dict = connection.settings_dict

        alternative_args = [] if not alternative_args else alternative_args

        args, env = DatabaseClient.settings_to_cmd_args_env(settings_dict,
                                                            alternative_args)

        # patch the binary name
        args[0] = binary_name

        return args, (env or None)

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
