# -*- coding: utf-8 -*-
"""
This software is licensed under the License (MIT) located at
https://github.com/ephreal/rollbot/Licence

Please see the license for any restrictions or rights granted to you by the
License.
"""

from datetime import datetime


async def uptime_calculation(bot, curr_time=None):
    """
    Calculates the uptime based on the passed in bot boot time and the current
    time passed in. Current time is remaining passed in to assist with testing
    of the code.

    bot: discord.ext.commands.Bot()
    curr_time: datetime.now()
        -> uptime: string
    """
    if not curr_time:
        curr_time = datetime.now()

    difference = curr_time - bot.boot_time
    days = difference.days
    difference = difference.seconds

    difference %= 86400

    hours = difference // 3600
    difference %= 3600

    minutes = difference // 60
    seconds = difference % 60

    message = f"The bot has been up for {days} days, " \
              f"{hours} hours, {minutes} minutes, and {seconds} seconds"

    return message
