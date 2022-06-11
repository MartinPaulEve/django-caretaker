import djclick as click

from caretaker.backend.abstract_backend import BackendNotFoundError
from caretaker.frontend.abstract_frontend import FrontendNotFoundError
from caretaker.frontend.abstract_frontend import FrontendFactory
from caretaker.utils import log


@click.command()
@click.argument('output-directory')
@click.option('--backend-name', '-b',
              help='The name of the backend to use',
              type=str)
@click.option('--frontend-name', '-f',
              help='The name of the frontend to use',
              type=str)
def command(output_directory: str, backend_name: str, frontend_name: str) \
        -> None:
    """
    Output terraform files to the specified OUTPUT-DIRECTORY
    """
    logger = log.get_logger('caretaker')

    try:
        frontend, backend = FrontendFactory.get_frontend_and_backend(
            backend_name=backend_name,
            frontend_name=frontend_name,
            raise_on_none=True
        )

        frontend.generate_terraform(
            output_directory=output_directory,
            backend=backend
        )
    except BackendNotFoundError:
        logger.error('Unable to find a valid backend')
    except FrontendNotFoundError:
        logger.error('Unable to find a valid frontend')
