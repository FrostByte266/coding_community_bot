from datetime import datetime
import json
import os
import re

import asyncio

from discord import Embed
from discord.ext import commands,tasks
from discord.utils import get

class CodingBot:

	def __init__(self, config_file):
		self.config_file_path = config_file
		(self.config, self.bot_token) = self.load_config_and_fetch_token(config_file)
		self.bot = self.build_bot()
		self.load_cogs()

	def load_config_and_fetch_token(self, config_file):
		"""
		Loads bot configuration for use.
		"""
		token = None
		try:
			# Attempt to fetch the token from config.json
			config = json.loads(open(config_file, 'r').read())
			token = config['token']
			return (config, token)
		except FileNotFoundError:
			# If config.json does not exist, it must be the first time starting the
			# bot, run through configuration
			# If we are running from a docker container, fetch the token through an
			# environment variable, otherwise, prompt the user to enter it
			token_env = os.environ.get('BOT_TOKEN', None)
			prefix_env = os.environ.get('BOT_PREFIX', None)
			token = token_env if token_env is not None else input(
				'It appears this is the first time running the bot. '
				'Please enter your bot\'s token: ')

			prefix = prefix_env if prefix_env is not None else input(
				'Please enter the prefix for your bot '
			) 

			initial_config = {
				'token': token,
				'prefix': prefix
			}

			json.dump(initial_config, open(config_file, 'w'),
				indent=2, separators=(',', ': '))

			os.makedirs('./assets/network_charts', exist_ok=True)
			os.makedirs('./assets/role_charts', exist_ok=True)
			
			return (initial_config, token)

	def refresh_config(self, new_config, write=True):
		self.config = new_config
		if write:
			json.dump(new_config, open(self.config_file_path, 'w'),
						indent=2, separators=(',', ': '))

	def load_cogs(self):
		for file in os.listdir('./cogs'):
			if file.endswith('.py'):
				try:
					self.bot.load_extension(f'cogs.{file[:-3]}')
				except Exception as e:
					print(f"Failed to load cog {file}")
					print(f"Error:\n{e}")

	def run_bot(self):
		loop = asyncio.get_event_loop()
		try:
			loop.run_until_complete(self.bot.start(self.bot_token))
		except Exception as e:
			print("Error", e)
		print("Restarting...")

	def build_bot(self):
		bot = commands.Bot(command_prefix=self.config['prefix'])

		@bot.event
		async def on_ready():
			print("Ready")
			config = json.loads(open('assets/config.json', 'r').read())

			# Check if there are any new servers the bot does not have configs for
			for server in bot.guilds:
				if str(server.id) not in config:
					# Add empty config to JSON + initialize all user win/loss stats
					self.config[str(server.id)] = {
						"verification_role": None,
						"reporting_channel": None,
						"reddit_channel": None,
						"reports": {}
					}
					# Save to config file
					self.refresh_config(self.config)


		@tasks.loop(seconds=86400)
		async def kick_unverified_task():
			guild_id_to_monitor = 697292778215833652
			guild = bot.get_guild(guild_id_to_monitor)
			guild_members = guild.members
			unverified_role = get(guild.roles, name="Unverified")
			unverified_members = unverified_role.members

			if datetime.today().weekday() !=6:
				for member in unverified_members:
					await member.send(
							"Automated Sunday Kick Warning: You will be kicked end of day Sunday if you do not " \
							"introduce yourself in #if-you-are-new-click here within the Coding Community server."
						)
				else:
					for member in unverified_members:
						await member.send(
											"Automated Sunday Kick Warning: You will be kicked in 5 minutes if you do not " \
											"introduce yourself in #if-you-are-new-click here within the Coding Community server."
										)

					await asyncio.sleep(300)

					reason = "Automated weekly kick due to not introducing yourself in the #if-you-are-new-click-here channel"
					for member in unverified_members:
						await guild.kick(member, reason=reason)

		@bot.event
		async def on_message(message):
			if message.guild is None:
				return await bot.process_commands(message)
			elif message.author == bot.user:
				return

			config = self.config[str(message.guild.id)]
			verification_enabled = True if config["verification_role"] is not None else False
			unverified_role = get(message.author.guild.roles, name="Unverified")

			if str(message.channel) == 'if-you-are-new-click-here' and message.content is not None:
				words_split = message.content.replace(":", " ").split()
				word_group = list(re.sub("(,|\.|:)$", "", word) for word in words_split)
				word_group.extend(words_split)

				#run word_group through set as a filter to force unique words
				word_group = list(set(word_group))

				ignored_roles = ['@everyone', 'Admin', 'Spartan Mod','Moderator', 'Owner', 'Staff',
								'Merit Badge (lvl - Moderator)',
								'Merit Badge (lvl - Admin)',
								'Merit Badge (lvl - Owner)','BOT', 'little fox familiar']

				roles = {role.name.lower():role for role in message.guild.roles if role.name not in ignored_roles}
				member_roles = [roles.get(word.lower(), 0) for word in word_group if roles.get(word.lower(), 0) != 0]
				await message.author.add_roles(*member_roles)

				newline = '\n'
				await message.author.send(
					f'Hello, based on your introduction, you have automatically been assigned the following roles: \n'
					f'{newline.join([role.name for role in member_roles])} \n'
					'If you believe you are missing some roles or have received roles that do not apply to you, '
					'please feel free to contact the moderation team'
				)
				if verification_enabled:
					await message.author.remove_roles(unverified_role)
			elif verification_enabled and str(message.channel) != 'if-you-are-new-click-here' and unverified_role in message.author.roles:
				await message.author.send("Before you can send messages you need to introduce yourself in #if-you-are-new-click-here."\
										" Please state any programming languages you have used, as well as whether you are a"\
										"Beginner, Novice, Advanced, or Professional. You can review earlier introductions in "\
										"the #if-you-are-new-click-here channel for examples.")
				await message.delete()
			await bot.process_commands(message)

		@bot.event
		async def on_member_join(member):
			config = self.config[str(member.guild.id)]
			verification_enabled = True if config["verification_role"] is not None else False
			if verification_enabled and not member.bot:
				role = get(member.guild.roles, id=config["verification_role"])
				await member.add_roles(role)

			with open('assets/welcome_message.txt') as f:
				message = f.read()
			await member.send(message)

			# Prepare welcome embed
			embed = Embed(
				color=0x9370DB,
				description=f'Welcome to the server! You are member number {len(list(member.guild.members))}'
			)
			embed.set_thumbnail(url=member.avatar_url)
			embed.set_author(name=member.name, icon_url=member.avatar_url)
			embed.set_footer(text=member.guild, icon_url=member.guild.icon_url)
			embed.timestamp = datetime.utcnow()

			# Get the server message channel and send welcome message there
			channel = bot.get_channel(id=member.guild.system_channel.id)

			await channel.send(embed=embed)

		@bot.event
		async def on_member_remove(member):
			# Prepare goodbye embed
			embed = Embed(color=0x9370DB, description=f'Goodbye! Thank you for spending time with us!')
			embed.set_thumbnail(url=member.avatar_url)
			embed.set_author(name=member.name, icon_url=member.avatar_url)
			embed.set_footer(text=member.guild, icon_url=member.guild.icon_url)
			embed.timestamp = datetime.utcnow()

			# Get the server message channel and send goodbye message there
			channel = bot.get_channel(id=member.guild.system_channel.id)

			await channel.send(embed=embed)

		@bot.event
		async def on_guild_join(guild):
			# Create configuration dict to store in JSON
			self.config[str(guild.id)] = {
				"verification_role": None,
				"reporting_channel": None,
				"reddit_channel": None,
				"reports": {}
			}
			# Save to config file
			self.refresh_config(config)

		@bot.event
		async def on_guild_remove(guild):
			self.config.pop(str(guild.id))
			self.refresh_config(self.config)

		return bot
