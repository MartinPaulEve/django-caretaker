import djclick as click
from django.db import DEFAULT_DB_ALIAS, transaction

from caretaker.frontend.abstract_frontend import FrontendFactory, \
    FrontendNotFoundError
from caretaker.utils import log, file


@click.command()
@click.argument('input-file', type=str)
@click.option('--database', '-d', help="The database to use",
              default=DEFAULT_DB_ALIAS)
@click.option('--frontend-name', '-f',
              help='The name of the frontend to use',
              type=str)
@click.option('--alternative-binary', '-a',
              help='The alternative binary to use',
              type=str, default='')
@click.option('--alternative-arguments',
              help='The alternative arguments to use',
              type=str, default='')
@click.option('--dry-run', '-d', is_flag=True, help="Run in dry mode.")
def command(input_file: str, frontend_name: str,
            database: str = DEFAULT_DB_ALIAS,
            alternative_binary: str = '', alternative_arguments: str = '',
            dry_run: bool = False) -> None:
    """
    Imports INPUT-FILE back into the system. Warning: overwrites database and FS
    """

    database = database if database else DEFAULT_DB_ALIAS

    with transaction.atomic(using=database):
        logger = log.get_logger('command')

        if dry_run:
            logger.info('Operating in dry-run mode. Nothing will be changed.')

        try:
            frontend = FrontendFactory.get_frontend(frontend_name=frontend_name,
                                                    raise_on_none=True)

            alternative_arguments = alternative_arguments.split(' ') \
                if alternative_arguments else None

            frontend.import_file(
                database=database, alternative_binary=alternative_binary,
                alternative_args=alternative_arguments, input_file=input_file,
                raise_on_error=False, dry_run=dry_run
            )

        except FrontendNotFoundError:
            logger.error('Unable to find a valid frontend')
        except PermissionError:
            logger.error('Unable to open output file {}'.format(input_file))
