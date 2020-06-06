import logging
import os


def setup_logging(bot, log="discord.log"):
    """
    Sets up the bot log with the following defaults

    Default log level: 50  (CRITICAL)
    Default log name: discord.log

    bot: discord.ext.commands.Bot()
    log: string
        -> None
    """

    # Rotate logs
    old_log_path = f'{log}.old'
    if os.path.exists(old_log_path):
        os.remove(old_log_path)
    if os.path.exists(log):
        os.rename(log, old_log_path)

    bot.logger = logging.getLogger('discord')
    bot.logger.setLevel(logging.WARNING)
    bot.handler = logging.FileHandler(filename=log,
                                      encoding='utf-8', mode='w')
    bot.handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:'
                                               '%(name)s: %(message)s'))
    bot.logger.addHandler(bot.handler)


async def set_logging_level(bot, log_level):
    """
    Python's logger has 5 log level that are of use to us here. From most
    verbose to least, they are:
        DEBUG
        INFO
        WARNING
        ERROR
        CRITICAL
    """

    bot.logger.setLevel(log_level)
