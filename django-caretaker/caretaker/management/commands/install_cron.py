import os

from crontab import CronTab, CronItem
from django.conf import settings

from caretaker.utils import log, file

import djclick as click


@click.command()
@click.option('--dry-run', '-d', is_flag=True, help="Run in dry mode.")
def command(dry_run: bool) -> CronTab:
    """
    Installs crontab entries to run at 00:15 every day
    """
    return install_cron(job_name=settings.CARETAKER_BACKUP_BUCKET,
                        commit=not dry_run, base_dir=settings.BASE_DIR)


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


def install_cron(job_name: str, base_dir: str, commit: bool = True) \
        -> CronTab | None:
    """
    Installs a crontab entry to run the backup daily

    :param job_name: the name of the cron job
    :param base_dir: the working directory from which to operate
    :param commit: whether to write the crontab to disk or just print
    :return:
    """
    tab = CronTab(user=True)

    base_dir = file.normalize_path(base_dir)

    return _install_cron(job_name=job_name, base_dir=str(base_dir),
                         commit=commit, tab=tab)


def _install_cron(job_name: str, base_dir: str, tab: CronTab,
                  commit: bool = True) \
        -> CronTab | None:
    """
    Installs a crontab entry to run the backup daily

    :param job_name: the name of the cron job
    :param base_dir: the working directory from which to operate
    :param commit: whether to write the crontab to disk or just print
    :param tab: the crontab to use
    :return:
    """
    logger = log.get_logger('cron')

    jobs = [
        {
            'name': 'caretaker_sync_{}_job'.format(job_name),
            'task': 'run_backup',
        },
    ]

    virtualenv = os.environ.get('VIRTUAL_ENV', None)

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

    if commit:
        tab.write()

    return tab
