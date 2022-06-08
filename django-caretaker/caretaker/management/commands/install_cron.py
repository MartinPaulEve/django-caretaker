import os

from crontab import CronTab
from django.conf import settings
from django.core.management.base import BaseCommand

from caretaker.utils import log, file


def find_job(tab, comment):
    for job in tab:
        if job.comment == comment:
            return job
    return None


class Command(BaseCommand):
    """
    Installs cron tasks.
    """

    help = "Installs cron tasks."

    def add_arguments(self, parser):
        parser.add_argument('--action', default="")

    def handle(self, *args, **options):
        """Installs Cron jobs
        """
        self.install_cron(job_name=settings.CARETAKER_BACKUP_BUCKET,
                          action=options.get('action'),
                          base_dir=settings.BASE_DIR)

    @staticmethod
    def install_cron(job_name: str, action: str, base_dir: str) \
            -> CronTab | None:
        logger = log.get_logger('caretaker-cron')
        tab = CronTab(user=True)
        virtualenv = os.environ.get('VIRTUAL_ENV', None)

        base_dir = file.normalize_path(base_dir)

        jobs = [
            {
                'name': 'caretaker_sync_{}_job'.format(job_name),
                'task': 'run_backup',
            },
        ]

        for job in jobs:
            current_job = find_job(tab, job['name'])

            if not current_job:
                django_command = "{0}/manage.py {1}".format(str(base_dir),
                                                            job['task'])
                command = '%s/bin/python3 %s' % (virtualenv, django_command)

                cron_job = tab.new(command, comment=job['name'])
                cron_job.setall("15 0 * * *")

            else:
                logger.info("{name} cron job already exists.".format(
                    name=job['name']))

        if action == 'test':
            logger.info(tab.render())
        elif action == 'quiet':
            pass
        else:
            tab.write()

        return tab
