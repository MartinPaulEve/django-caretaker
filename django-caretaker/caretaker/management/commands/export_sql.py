import os

from crontab import CronTab, CronItem
from django.conf import settings

from caretaker.frontend.abstract_frontend import FrontendFactory, \
    FrontendNotFoundError
from caretaker.utils import log, file

import djclick as click


@click.command()
@click.option('--database', '-d', help="The database to use", default='')
@click.option('--frontend-name', '-f',
              help='The name of the frontend to use',
              type=str)
def command(database: str, frontend_name: str) -> str:
    """
    Exports SQL files from the database
    """

    logger = log.get_logger('caretaker-command')

    try:
        frontend = FrontendFactory.get_frontend(frontend_name=frontend_name,
                                                raise_on_none=True)

        return frontend.export_sql(database)
    except FrontendNotFoundError:
        logger.error('Unable to find a valid frontend')
