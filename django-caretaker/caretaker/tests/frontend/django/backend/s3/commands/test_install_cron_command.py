from unittest.mock import patch

import django
from django.conf import settings
from moto import mock_s3

from caretaker.management.commands import install_cron
from caretaker.tests.frontend.django.backend.s3.caretaker_test import \
    AbstractDjangoS3Test


@mock_s3
class TestInstallCronCommand(AbstractDjangoS3Test):
    def setUp(self):
        self.logger.info('Setup for install cron command')

        self.create_bucket()

        django.setup()

    def tearDown(self):
        self.logger.info('Teardown for install cron command')
        pass

    @patch('crontab.CronTab.write')
    def test(self, cron_mock):
        self.logger.info('Testing create_backup')

        tab = install_cron.command.callback(dry_run=True,)

        self.assertIsNotNone(tab)
        self.assertTrue(
            'caretaker_sync_{}_job'.format(self.bucket_name) in tab.render())

        # run it again to simulate finding the existing job
        tab = install_cron._install_cron(
            job_name=settings.CARETAKER_BACKUP_BUCKET,
            commit=False,
            base_dir=settings.BASE_DIR, tab=tab)

        self.assertIsNotNone(tab)
        self.assertTrue(
            'caretaker_sync_{}_job'.format(self.bucket_name) in tab.render())

        # now check that when we run the save method, it does so
        tab = install_cron.command.callback(dry_run=False, )
        cron_mock.assert_called()

        job = install_cron.find_job(tab,
                                    'caretaker_sync_{}_job'.format(
                                        self.bucket_name))

        self.assertIsNotNone(job)

        job = install_cron.find_job(tab,
                                    'NO THIS AIN\'T FOUND')

        self.assertIsNone(job)

