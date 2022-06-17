import logging

import django
from django.test import TestCase
from testfixtures import log_capture

from caretaker.utils import log


class LoggerDefaultTestCase(TestCase):
    @log_capture()
    def test_root(self, captures):
        logger = log.get_logger(level=logging.DEBUG)
        logger.debug("a noise")
        logger.info("a message")
        logger.warning("a warning")
        logger.error("an error")
        logger.critical("a critical error")
        captures.check(
            ("django-caretaker-root", "DEBUG", "a noise"),
            ("django-caretaker-root", "INFO", "a message"),
            ("django-caretaker-root", "WARNING", "a warning"),
            ("django-caretaker-root", "ERROR", "an error"),
            ("django-caretaker-root", "CRITICAL", "a critical error"),
        )

    @log_capture()
    def test_django(self, captures):
        logger = log.get_logger('django')
        logger.debug("a noise")
        logger.info("a message")
        logger.warning("a warning")
        logger.error("an error")
        logger.critical("a critical error")
        captures.check(
            ("django-caretaker-django", "INFO", "a message"),
            ("django-caretaker-django", "WARNING", "a warning"),
            ("django-caretaker-django", "ERROR", "an error"),
            ("django-caretaker-django", "CRITICAL", "a critical error"),
            )
