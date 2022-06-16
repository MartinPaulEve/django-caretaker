import djclick as click
from django.db import DEFAULT_DB_ALIAS, transaction

from caretaker.frontend.abstract_frontend import FrontendFactory, \
    FrontendNotFoundError
from caretaker.utils import log, file


@click.command()
@click.option('--database', '-d', help="The database to use",
              default=DEFAULT_DB_ALIAS)
@click.option('--frontend-name', '-f',
              help='The name of the frontend to use',
              type=str)
@click.option('--output-file', '-o',
              help='An output file to read (or stdout)',
              type=str, default='-')
@click.option('--alternative-binary', '-a',
              help='The alternative binary to use',
              type=str, default='')
@click.option('--alternative-arguments',
              help='The alternative arguments to use',
              type=str, default='')
def command(frontend_name: str, database: str = DEFAULT_DB_ALIAS,
            output_file: str = '-',
            alternative_binary: str = '', alternative_arguments: str = ''
            ) -> None:
    """
    Exports SQL files from the database
    """
    database = database if database else DEFAULT_DB_ALIAS

    with transaction.atomic(using=database):
        logger = log.get_logger('caretaker-command')

        try:
            frontend = FrontendFactory.get_frontend(frontend_name=frontend_name,
                                                    raise_on_none=True)

            if output_file != '-':
                output_file = str(file.normalize_path(output_file))

            alternative_arguments = alternative_arguments.split(' ') \
                if alternative_arguments else None

            frontend.export_sql(
                database=database, alternative_binary=alternative_binary,
                alternative_args=alternative_arguments, output_file=output_file
            )

        except FrontendNotFoundError:
            logger.error('Unable to find a valid frontend')
        except PermissionError:
            logger.error('Unable to open output file {}'.format(output_file))
