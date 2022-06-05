from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from caretaker.main_utils import log
from caretaker.main_utils.zip import create_zip_file


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Creates a local backup set"

    def add_arguments(self, parser):
        parser.add_argument('--output-directory')

    def handle(self, *args, **options):
        """
        Creates a local backup set
        """

        self._create_backup(options.get('output_directory'))

    @staticmethod
    def _create_backup(output_directory, data_file='data.json',
                       archive_file='media.zip', path_list=None):
        logger = log.get_logger('caretaker')

        if not output_directory:
            logger.error('No output directory specified')
            return None, None

        output_directory = Path(output_directory).expanduser()

        # create the directory if needed
        output_directory.mkdir(parents=True, exist_ok=True)

        # setup redirect so that we can pipe the output of dump data to
        # our output file
        buffer = StringIO()
        call_command('dumpdata', stdout=buffer)
        buffer.seek(0)

        with (output_directory / data_file).open('w') as out_file:
            out_file.write(buffer.read())
            logger.info('Wrote {}'.format(data_file))

        # now create a tarball of the media directory and any others specified
        path_list = [] if not path_list else path_list
        path_list = list(set(path_list))

        if settings.MEDIA_ROOT and settings.MEDIA_ROOT not in path_list:
            path_list.append(settings.MEDIA_ROOT)

        path_list_final = [Path(path).expanduser().resolve(strict=True)
                           for path in path_list]

        zip_file = create_zip_file(
            input_paths=path_list_final,
            output_file=Path(output_directory / archive_file)
        )

        logger.info('Wrote {} ({})'.format(archive_file, zip_file))

        return output_directory / data_file, zip_file
