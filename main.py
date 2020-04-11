import importlib
import json
import os

from bot import CodingBot

if __name__ == '__main__':
	while not os.path.exists('poweroff'):
		Bot = CodingBot('assets/config.json', prefix='!')
		Bot.run_bot()
		importlib.reload(bot)

	# Remove the file "poweroff" so it'll turn on next time
	os.remove('poweroff')
