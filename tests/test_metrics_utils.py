# -*- coding: utf-8 -*-
"""
This software is licensed under the License (MIT) located at
https://github.com/ephreal/rollbot/Licence

Please see the license for any restrictions or rights granted to you by the
License.
"""

import asyncio
import unittest
from datetime import datetime
from unittest.mock import Mock
from utils import metrics_utils


class TestBotMetrics(unittest.TestCase):
    def setUp(self):
        pass

    def test_uptime_calculation(self):
        """Verifies that the uptime calculation is done correctly"""

        bot = Mock()
        bot.boot_time = datetime.fromtimestamp(1577836800)
        now = datetime.fromtimestamp(1578007403)

        uptime = run(metrics_utils.uptime_calculation(bot, now))
        expected = f"The bot has been up for 1 days, " \
                   f"23 hours, 23 minutes, and 23 seconds"

        self.assertEqual(uptime, expected)


def run(coroutine):
    """
    Runs and returns the data from the couroutine passed in. This is to
    only be used in unittesting.

    coroutine : asyncio coroutine

        -> coroutine return
    """

    return asyncio.get_event_loop().run_until_complete(coroutine)
