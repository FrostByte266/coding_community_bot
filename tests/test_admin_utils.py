import asyncio
import os
import unittest
from unittest.mock import Mock
from utils import admin_utils


class TestAdminUtils(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        """Removes test log files if they still exist after the tests run"""
        if os.path.exists("test_log.log"):
            os.remove("test_log.log")

        if os.path.exists("test_log.log.old"):
            os.remove("test_log.log.old")

    def test_setup_logging(self):
        """Verify that the logger exists and is at the right debug level"""
        bot = Mock()
        admin_utils.setup_logging(bot, "test_log.log")
        self.assertEqual(bot.logger.level, 50)
        self.assertTrue(os.path.exists("test_log.log"))
        bot.logger.log(msg="Hello world!", level=50)

        with open("test_log.log", 'r') as f:
            log = f.read()

        self.assertTrue("Hello world!" in log)

    def test_set_logging_level(self):
        """Verifies the logging level can be changed"""
        bot = Mock()
        admin_utils.setup_logging(bot, "test_log.log")
        run(admin_utils.set_logging_level(bot, "DEBUG"))
        self.assertEqual(bot.logger.level, 10)


def run(coroutine):
    """
    Runs and returns the data from the couroutine passed in. This is to
    only be used in unittesting.

    coroutine : asyncio coroutine

        -> coroutine return
    """

    return asyncio.get_event_loop().run_until_complete(coroutine)
