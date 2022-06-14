from unittest.mock import patch

import django
from django.conf import settings
from moto import mock_s3

from crontab import CronTab

from caretaker.management.commands import install_cron
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test


@mock_s3
class TestInstallCronCommand(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for create_backup')

        self.create_bucket()

        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for create_backup')
        pass

    @patch('crontab.CronTab.write')
    def test(self, cron_mock):
        self.logger.info('Testing create_backup')

        tab = install_cron.command.callback(dry_run=True,)

        self.assertIsNotNone(tab)
        self.assertTrue(
            'caretaker_sync_caretakertestbackup_job' in tab.render())

        # run it again to simulate finding the existing job
        tab = install_cron._install_cron(
            job_name=settings.CARETAKER_BACKUP_BUCKET,
            commit=False,
            base_dir=settings.BASE_DIR, tab=tab)

        self.assertIsNotNone(tab)
        self.assertTrue(
            'caretaker_sync_caretakertestbackup_job' in tab.render())

        # now check that when we run the save method, it does so
        tab = install_cron.command.callback(dry_run=False, )
        cron_mock.assert_called()

        job = install_cron.find_job(tab,
                                    'caretaker_sync_caretakertestbackup_job')

        self.assertIsNotNone(job)

        job = install_cron.find_job(tab,
                                    'NO THIS AIN\'T FOUND')

        self.assertIsNone(job)

