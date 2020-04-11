import asyncio
import bot
import importlib
import json
import os
import sys


def load_config():
	"""
	Loads bot configuration for use.
	"""
	token = None
	try:
		# Attempt to fetch the token from config.json
		token = json.loads(open('assets/config.json', 'r').read())['token']
	except FileNotFoundError:
		# If config.json does not exist, it must be the first time starting the
		# bot, run through configuration
		# If we are running from a docker container, fetch the token through an
		# environment variable, otherwise, prompt the user to enter it
		environment = os.environ.get('BOT_TOKEN', None)
		token = environment if environment is not None else input(
			'It appears this is the first time running the bot. '
			'Please enter your bot\'s token: ')

		initial_config = {"token": token}

		json.dump(initial_config, open('assets/config.json', 'w'),
				  indent=2, separators=(',', ': '))

		os.mkdir('./assets/network_charts')
		os.mkdir('./assets/role_charts')

	finally:
		return token

def run_client(client, *args, **kwargs):
	loop = asyncio.get_event_loop()
	try:
		loop.run_until_complete(client.start(*args, **kwargs))
	except Exception as e:
		print("Error", e)
	print("Restarting...")

if __name__ == "__main__":

	token = load_config()

	while not os.path.exists("poweroff"):
		Bot = bot.CodingBot(prefix='!')
		run_client(Bot.bot, token)
		importlib.reload(bot)

	# Remove the file "poweroff" so it'll turn on next time
	os.remove("poweroff")
	sys.exit()
