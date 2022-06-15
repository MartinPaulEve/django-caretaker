import abc
import logging

from django.db.backends.base.base import BaseDatabaseWrapper


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
    def handles(self) -> str:
        """
        The database engine that this class handles

        :return: a string of the database name (e.g. django.db.backends.sqlite3)
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def export_sql(connection: BaseDatabaseWrapper) -> str:
        """
        Export SQL from the database using the specific provider

        :return: a string of the database to output
        """
        pass

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
