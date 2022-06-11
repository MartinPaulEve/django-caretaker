import djclick as click
import humanize
from django.conf import settings

from caretaker.backend.abstract_backend import BackendNotFoundError
from caretaker.frontend.abstract_frontend import FrontendNotFoundError
from caretaker.frontend.abstract_frontend import FrontendFactory
from caretaker.utils import log


@click.command()
@click.argument('remote-key')
@click.option('--backend-name', '-b',
              help='The name of the backend to use',
              type=str)
@click.option('--frontend-name', '-f',
              help='The name of the frontend to use',
              type=str)
def command(remote_key: str, backend_name: str, frontend_name: str) \
        -> None:
    """
    Lists remote versions of REMOTE-KEY (a filename)
    """
    logger = log.get_logger('caretaker')

    try:
        frontend, backend = FrontendFactory.get_frontend_and_backend(
            backend_name=backend_name,
            frontend_name=frontend_name,
            raise_on_none=True
        )

        results = frontend.list_backups(
            backend=backend, remote_key=remote_key,
            bucket_name=settings.CARETAKER_BACKUP_BUCKET)

        for item in results:
            logger.info('Backup from {}: {} [{}]'.format(
                item['last_modified'],
                item['version_id'],
                humanize.naturalsize(item['size'])
            ))
    except BackendNotFoundError:
        logger.error('Unable to find a valid backend')
    except FrontendNotFoundError:
        logger.error('Unable to find a valid frontend')
