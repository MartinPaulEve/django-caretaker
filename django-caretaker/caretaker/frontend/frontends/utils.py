import contextlib
import importlib
import select
import subprocess
import sys

from django.db.backends.base.base import BaseDatabaseWrapper


class DatabasePatcher:
    @staticmethod
    def patch_exporter(database: BaseDatabaseWrapper) -> (bool, object):
        module_dict = {
            'caretaker.frontend.frontends.database_exporters.django.sqlite':
                'SQLiteDatabaseExporter',
            'caretaker.frontend.frontends.database_exporters.django.postgres':
                'PostgresDatabaseExporter',
            'caretaker.frontend.frontends.database_exporters.django.mysql':
                'MysqlDatabaseExporter',
        }

        for module_name, class_name in module_dict.items():
            # load the modules to see if we find a match
            module = importlib.import_module(module_name)
            class_ref = getattr(module, class_name)
            patcher = class_ref()

            # patch the underlying module
            if patcher.patch(database):
                return True, patcher

        return False, None

    @staticmethod
    def patch_importer(database: BaseDatabaseWrapper) -> (bool, object):
        module_dict = {
            'caretaker.frontend.frontends.database_importers.django.sqlite':
                'SQLiteDatabaseImporter',
        }

        for module_name, class_name in module_dict.items():
            # load the modules to see if we find a match
            module = importlib.import_module(module_name)
            class_ref = getattr(module, class_name)
            patcher = class_ref()

            # patch the underlying module
            if patcher.patch(database):
                return True, patcher

        return False, None

    @staticmethod
    def can_handle(database: BaseDatabaseWrapper, patcher) -> bool:
        return patcher.handles in database.settings_dict['ENGINE']


class BufferedProcessReader:
    """
    A class to read files in a neatly buffered way that can handle large output
    """

    proc: subprocess.Popen = None

    def __init__(self, process: subprocess.Popen):
        self.proc = process

    def handle_process(self, output_filename: str = '-'):
        """
        Process the output from an external command

        :param output_filename: the output filename or '-' for stdout
        :return:
        """
        with smart_open(output_filename) as out_file:
            reached_end = False
            while (self.proc.returncode is None) or (not reached_end):
                self.proc.poll()
                reached_end = False

                select.select([self.proc.stdout], [], [], float(1.0))

                data = self.proc.stdout.read(1024)
                if len(data) == 0:  # Read of zero bytes means EOF
                    reached_end = True
                else:
                    # pass it to the buffer
                    if out_file is sys.stdout:
                        out_file.write(data.decode('utf-8'))
                    else:
                        out_file.write(data)
                    out_file.flush()


@contextlib.contextmanager
def smart_open(filename: str = None):
    """
    Opens a file for binary writing or stdout for text writing

    :param filename: the filename to open or "-" for stdout
    :return: a file handle or stdout
    """
    if filename and filename != '-':
        fh = open(filename, 'wb')
    else:
        fh = sys.stdout
    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()


def ternary_switch(primary: object, secondary: object) -> object:
    """
    Return primary if not secondary

    :param primary: the first object
    :param secondary: the second object
    :return: primary if secondary doesn't exist, else secondary
    """
    return primary if not secondary else secondary
