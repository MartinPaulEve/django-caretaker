import djclick as click

from caretaker.frontend.abstract_frontend import FrontendFactory, \
    FrontendNotFoundError

from caretaker.utils import log


@click.command()
@click.argument('output-directory')
@click.option('--additional-files', '-a', multiple=True,
              help='Additional directories to add to the zip file',
              type=str)
@click.option('--frontend-name', '-f',
              help='The name of the frontend to use',
              type=str)
def command(output_directory: str, additional_files: tuple,
            frontend_name: str = '') -> None:
    """
    Create a local backup archive in the specified OUTPUT-DIRECTORY
    """
    logger = log.get_logger('caretaker')

    try:
        frontend = FrontendFactory.get_frontend(frontend_name=frontend_name,
                                                raise_on_none=True)

        frontend.create_backup(output_directory=output_directory,
                               path_list=list(additional_files))
    except FrontendNotFoundError:
        logger.error('Unable to find a valid frontend')
