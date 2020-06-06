import importlib
import json
import os

import bot

if __name__ == '__main__':
    while not os.path.exists('poweroff'):
        Bot = bot.CodingBot('assets/config.json')
        Bot.start_logging()
        Bot.run_bot()
        Bot.stop_logging()
        importlib.reload(bot)

    # Remove the file "poweroff" so it'll turn on next time
    os.remove('poweroff')
