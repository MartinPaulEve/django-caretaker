import os

from crontab import CronTab, CronItem
from django.conf import settings

from caretaker.utils import log, file

import djclick as click


@click.command()
@click.argument('action', default='')
def command(action: str) -> None:
    """
    Installs crontab entries to run at 00:15 every day
    """
    install_cron(job_name=settings.CARETAKER_BACKUP_BUCKET,
                 action=action, base_dir=settings.BASE_DIR)


def find_job(tab: CronTab, comment: str) -> CronItem | None:
    """
    Locates an existing crontab entry

    :param tab: the Crontab object
    :param comment: the comment attached to the job
    :return: a CrontabItem or None
    """
    for job in tab:
        if job.comment == comment:
            return job
    return None


def install_cron(job_name: str, action: str, base_dir: str) \
        -> CronTab | None:
    """
    Installs a crontab entry to run the backup daily

    :param job_name: the name of the cron job
    :param base_dir: the working directory from which to operate
    :param action: the action to take ("test", "quiet", or ""). "Test" will perform a dry run. Quiet will exit silently with changes unsaved. An empty string will save the crontab file.
    :return:
    """
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
            cron_command = '%s/bin/python3 %s' % (virtualenv, django_command)

            cron_job = tab.new(cron_command, comment=job['name'])
            cron_job.setall("15 0 * * *")

        else:
            logger.info("{name} cron job already exists.".format(
                name=job['name']))

    if action == 'test':
        logger.info(tab.render())
    else:
        tab.write()

    return tab
