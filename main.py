import importlib
import json
import os

import bot

if __name__ == '__main__':
    while not os.path.exists('poweroff'):
        Bot = bot.CodingBot('assets/config.json')
        Bot.run_bot()
        importlib.reload(bot)

    # Remove the file "poweroff" so it'll turn on next time
    os.remove('poweroff')
