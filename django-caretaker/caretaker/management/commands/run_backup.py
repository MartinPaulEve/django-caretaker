import djclick as click
from django.conf import settings

from caretaker.backend.abstract_backend import BackendNotFoundError
from caretaker.frontend.abstract_frontend import FrontendFactory
from caretaker.frontend.abstract_frontend import FrontendNotFoundError
from caretaker.utils import log


@click.command()
@click.argument('output-directory')
@click.option('--additional-files', '-a', multiple=True,
              help='Additional directories to add to the zip file',
              type=str)
@click.option('--backend-name', '-b',
              help='The name of the backend to use',
              type=str)
@click.option('--frontend-name', '-f',
              help='The name of the frontend to use',
              type=str)
def command(output_directory: str, additional_files: tuple, backend_name: str,
            frontend_name: str) -> None:
    """
    Pushes LOCAL-FILE to the latest version of REMOTE-KEY
    """
    logger = log.get_logger('caretaker')

    try:
        frontend, backend = FrontendFactory.get_frontend_and_backend(
            backend_name=backend_name,
            frontend_name=frontend_name,
            raise_on_none=True
        )

        frontend.run_backup(output_directory=output_directory,
                            backend=backend,
                            bucket_name=settings.CARETAKER_BACKUP_BUCKET,
                            path_list=list(additional_files))

    except BackendNotFoundError:
        logger.error('Unable to find a valid backend')
    except FrontendNotFoundError:
        logger.error('Unable to find a valid frontend')
