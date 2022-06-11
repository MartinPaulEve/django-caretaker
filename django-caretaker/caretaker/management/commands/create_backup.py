from django.core.management.base import BaseCommand

from caretaker.frontend.abstract_frontend import FrontendFactory


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Creates a local backup set"

    def add_arguments(self, parser):
        parser.add_argument('--output-directory')
        parser.add_argument('-a', '--additional-files',
                            action='append', required=False)

    def handle(self, *args, **options):
        """
        Creates a set of local backup files via a command

        :param args: the parser arguments
        :param options: the parser options
        :return: None
        """

        frontend = FrontendFactory.get_frontend()

        frontend.create_backup(output_directory=options.get('output_directory'),
                               path_list=options.get('additional_files'))

