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
            ("root", "DEBUG", "a noise"),
            ("root", "INFO", "a message"),
            ("root", "WARNING", "a warning"),
            ("root", "ERROR", "an error"),
            ("root", "CRITICAL", "a critical error"),
        )

    @log_capture()
    def test_django(self, captures):
        logger = log.get_logger('django')
        logger.debug("a noise")
        logger.info("a message")
        logger.warning("a warning")
        logger.error("an error")
        logger.critical("a critical error")
        if django.VERSION < (1, 9):
            captures.check(
                ("django", "DEBUG", "a noise"),
                ("django", "INFO", "a message"),
                ("django", "WARNING", "a warning"),
                ("django", "ERROR", "an error"),
                ("django", "CRITICAL", "a critical error"),
            )
        else:
            captures.check(
                ("django", "INFO", "a message"),
                ("django", "WARNING", "a warning"),
                ("django", "ERROR", "an error"),
                ("django", "CRITICAL", "a critical error"),
            )

    @log_capture()
    def test_caretaker(self, captures):
        logger = log.get_logger('caretaker')
        logger.debug("a noise")
        logger.info("a message")
        logger.warning("a warning")
        logger.error("an error")
        logger.critical("a critical error")
        captures.check(
            ("caretaker", "INFO", "a message"),
            ("caretaker", "WARNING", "a warning"),
            ("caretaker", "ERROR", "an error"),
            ("caretaker", "CRITICAL", "a critical error"),
        )
