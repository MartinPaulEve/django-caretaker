import djclick as click
from django.conf import settings

from caretaker.backend.abstract_backend import BackendNotFoundError
from caretaker.frontend.abstract_frontend import FrontendFactory
from caretaker.frontend.abstract_frontend import FrontendNotFoundError
from caretaker.utils import log


@click.command()
@click.argument('remote-key')
@click.argument('local-file')
@click.argument('backup-version')
@click.option('--backend-name', '-b',
              help='The name of the backend to use',
              type=str)
@click.option('--frontend-name', '-f',
              help='The name of the frontend to use',
              type=str)
def command(remote_key: str, local_file: str, backup_version: str,
            backend_name: str, frontend_name: str) \
        -> None:
    """
    Saves BACKUP-VERSION of REMOTE-KEY into LOCAL-FILE
    """
    logger = log.get_logger('')

    try:
        frontend, backend = FrontendFactory.get_frontend_and_backend(
            backend_name=backend_name,
            frontend_name=frontend_name,
            raise_on_none=True
        )

        frontend.pull_backup(out_file=local_file,
                             remote_key=remote_key,
                             backend=backend,
                             bucket_name=settings.CARETAKER_BACKUP_BUCKET,
                             backup_version=backup_version)
    except BackendNotFoundError:
        logger.error('Unable to find a valid backend')
    except FrontendNotFoundError:
        logger.error('Unable to find a valid frontend')
    except FileNotFoundError:
        logger.error('Unable to write to {}'.format(local_file))
