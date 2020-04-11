import asyncio
import bot
import importlib
import json
import os
import sys

from traceback import print_tb


if __name__ == "__main__":
	while not os.path.exists("poweroff"):
		Bot = bot.CodingBot('assets/config.json', prefix='!')
		Bot.run_bot()
		importlib.reload(bot)

	# Remove the file "poweroff" so it'll turn on next time
	os.remove("poweroff")
	sys.exit()
