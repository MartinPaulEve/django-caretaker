import djclick as click
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, transaction

from caretaker.backend.abstract_backend import BackendNotFoundError
from caretaker.frontend.abstract_frontend import FrontendFactory
from caretaker.frontend.abstract_frontend import FrontendNotFoundError
from caretaker.utils import log


@click.command()
@click.option('--additional-files', '-a', multiple=True,
              help='Additional directories to add to the zip file',
              type=str)
@click.option('--backend-name', '-b',
              help='The name of the backend to use',
              type=str)
@click.option('--frontend-name', '-f',
              help='The name of the frontend to use',
              type=str)
@click.option('--sql-mode', '-s', is_flag=True,
              help='Whether to output SQL instead of standard JSON',
              type=bool)
@click.option('--database', '-d', help="The database to use",
              default=DEFAULT_DB_ALIAS)
@click.option('--alternative-binary', '-a',
              help='The alternative binary to use',
              type=str, default='')
@click.option('--alternative-arguments',
              help='The alternative arguments to use',
              type=str, default='')
@click.option('--data-file',
              help='The data filename to use',
              type=str, default='data.json')
@click.option('--archive-file',
              help='The archive filename to use',
              type=str, default='media.zip')
def command(additional_files: tuple, backend_name: str,
            frontend_name: str, sql_mode: bool = False,
            database: str = DEFAULT_DB_ALIAS, alternative_binary: str = '',
            alternative_arguments: str = '',
            data_file: str = 'data.json',
            archive_file: str = 'media.zip') -> None:
    """
    Pushes LOCAL-FILE to the latest version of REMOTE-KEY
    """
    database = database if database else DEFAULT_DB_ALIAS

    with transaction.atomic(using=database):
        logger = log.get_logger('caretaker')

        try:
            frontend, backend = FrontendFactory.get_frontend_and_backend(
                backend_name=backend_name,
                frontend_name=frontend_name,
                raise_on_none=True
            )

            frontend.run_backup(backend=backend,
                                bucket_name=settings.CARETAKER_BACKUP_BUCKET,
                                path_list=list(additional_files),
                                raise_on_error=True, sql_mode=sql_mode,
                                archive_file=archive_file, data_file=data_file,
                                alternative_binary=alternative_binary,
                                alternative_arguments=alternative_arguments)

        except BackendNotFoundError:
            logger.error('Unable to find a valid backend')
        except FrontendNotFoundError:
            logger.error('Unable to find a valid frontend')
