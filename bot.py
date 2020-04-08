from datetime import datetime
import json
import os
import re

from discord import Embed
from discord.ext import commands
from discord.utils import get

def build_bot(prefix="!"):
	bot = commands.Bot(command_prefix=prefix)

	@bot.event
	async def on_ready():
		print("Ready")
		config = json.loads(open('assets/config.json', 'r').read())

		#schedules the routine 'Kick unverified members' task
		bot.loop.create_task(kick_unverified_task())

		# Check if there are any new servers the bot does not have configs for
		for server in bot.guilds:
			if str(server.id) not in config:
				# Add empty config to JSON + initialize all user win/loss stats
				config[str(server.id)] = {
					"verification_role": None,
					"reporting_channel": None,
					"reports": {}
				}
				# Save to config file
				json.dump(config, open('assets/config.json', 'w'), indent=2, separators=(',', ': '))

	# async def kick_unverified_task():
	# 	while True:
	# 		guild_id_to_monitor = 697292778215833652
	# 		guild = bot.get_guild(guild_id_to_monitor)
	# 		guild_members = guild.members
	# 		if datetime.today().weekday() !=6:
	# 			for member in guild_members:
	# 				if 'Unverified' in (role.name for role in member.roles):
	# 					await member.send(
	# 										"Automated Sunday Kick Warning: You will be kicked end of day Sunday if you do not " \
	# 										"introduce yourself in #if-you-are-new-click here within the Coding Community server."
	# 									)
	# 		else:
	# 			for member in guild_members:
	# 				if 'Unverified' in (role.name for role in member.roles):
	# 					await member.send(
	# 										"Automated Sunday Kick Warning: You will be kicked in 5 minutes if you do not " \
	# 										"introduce yourself in #if-you-are-new-click here within the Coding Community server."
	# 									)

	# 			await asyncio.sleep(300)

	# 			reason = "Automated weekly kick due to not introducing yourself in the #if-you-are-new-click-here channel"
	# 			for member in guild_members:
	# 				if 'Unverified' in (role.name for role in member.roles):
	# 					await guild.kick(member, reason=reason)

	# 			await asyncio.sleep(86400)

	@bot.event
	async def on_message(message):
		if message.guild is None:
			return await bot.process_commands(message)
		elif message.author == bot.user:
			return

		config_full = json.loads(open('assets/config.json', 'r').read())
		config = config_full[str(message.guild.id)]
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
		config_full = json.loads(open('assets/config.json', 'r').read())
		config = config_full[str(member.guild.id)]
		verification_enabled = True if config["verification_role"] is not None else False
		if verification_enabled and not member.bot:
			role = get(member.guild.roles, id=config["verification_role"])
			await member.add_roles(role)

		message = open('assets/welcome_message.txt').read()
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
		config = json.loads(open('assets/config.json', 'r').read())
		# Create configuration dict to store in JSON
		config[str(guild.id)] = {
			"verification_role": None,
			"reporting_channel": None,
			"reports": {}
		}
		# Save to config file
		json.dump(config, open('assets/config.json', 'w'), indent=2, separators=(',', ': '))

	@bot.event
	async def on_guild_remove(guild):
		config = json.loads(open('assets/config.json', 'r').read())
		config.pop(str(guild.id))
		json.dump(config, open('assets/config.json', 'w'), indent=2, separators=(',', ': '))

	return bot

def load_cogs(bot):
	for file in os.listdir('./cogs'):
		if file.endswith('.py'):
			try:
				bot.load_extension(f'cogs.{file[:-3]}')
			except Exception as e:
				print(f"Failed to load cog {file}")
				print(f"Error:\n{e}")
"""
	for file in os.listdir('./cogs'):
		if file.endswith('.py'):
			bot.load_extension(f'cogs.{file[:-3]}')

	return bot
"""
