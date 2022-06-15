import logging
import os
import subprocess

from django.db.backends.base.base import BaseDatabaseWrapper

from caretaker.utils import log

from caretaker.frontend.frontends.database_exporters.\
    abstract_database_exporter import AbstractDatabaseExporter


class SQLiteDatabaseExporter(AbstractDatabaseExporter):
    """
    The SQLite database exporters
    """
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

    @staticmethod
    def export_sql(connection: BaseDatabaseWrapper) -> str:
        """
        Export SQL from the database using the specific provider

        :return: a string of the database to output
        """
        args = ['sqlite3', connection.settings_dict["NAME"], '.dump']
        env = None
        env = {**os.environ, **env} if env else None

        process = subprocess.Popen(args, env=env, stdout=subprocess.PIPE)

        outputs = process.communicate()
        final_output = []

        for output_line in outputs:
            if output_line:
                final_output.append(output_line.decode('utf-8'))

        return '\n'.join(final_output)

    def patch(self, connection: BaseDatabaseWrapper):
        """
        Export SQL from the database using the specific provider

        :param connection: the connection object
        :return: boolean of whether the object was patched
        """
        # determine if we can handle this

        connection.export_sql = self.export_sql
