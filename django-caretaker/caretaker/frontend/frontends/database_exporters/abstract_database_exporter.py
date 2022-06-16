import abc
import logging
from typing import TextIO
from typing.io import BinaryIO

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

    @abc.abstractmethod
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
