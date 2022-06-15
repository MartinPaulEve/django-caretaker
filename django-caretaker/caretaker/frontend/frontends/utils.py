import contextlib
import importlib
import select
import subprocess
import sys

from django.db.backends.base.base import BaseDatabaseWrapper


class DatabasePatcher:
    @staticmethod
    def patch(database: BaseDatabaseWrapper) -> (bool, object):
        module_dict = {
            'caretaker.frontend.frontends.database_exporters.django.sqlite':
                'SQLiteDatabaseExporter'
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

                ready = select.select([self.proc.stdout], [], [], float(1.0))

                if self.proc.stdout in ready[0]:
                    data = self.proc.stdout.read(1024)
                    if len(data) == 0:  # Read of zero bytes means EOF
                        reached_end = True
                    else:
                        # pass it to the buffer
                        out_file.write(data.decode('utf-8'))
                        out_file.flush()


@contextlib.contextmanager
def smart_open(filename: str = None):
    if filename and filename != '-':
        fh = open(filename, 'wb')
    else:
        fh = sys.stdout
    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()