"""
All commands in this cog are assumed to require administrator level permissions
to run. These commands are intended to make administration of the bot itself
easier.

Commands provided by this Cog

	- poweroff : Turns the bot off
	- reload   : Reloads the bot configuration from local files OR pulls from
				 github and then reloads.

"""

import os
import sys
import traceback

from discord.ext import commands
from discord import client
from subprocess import Popen, PIPE


class Admin(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@commands.command(hidden=True, description="Turns off the bot")
	@commands.has_permissions(administrator=True)
	async def poweroff(self, ctx):
		f"""
		Turns the bot off.

		Examples:
			Turn the bot off
			{self.bot.command_prefix}poweroff
		"""

		with open("poweroff", 'w') as f:
			f.write("Bot is stopping")

		shutdown_message = "Bot is being desummoned."
		await ctx.send(shutdown_message)
		await client.Client.logout(self.bot)

	@commands.command(hidden=True,
					  description="Reboots the bot")
	@commands.has_permissions(administrator=True)
	async def reboot(self, ctx):
		f"""
		Reboots the bot so all files can be reloaded.
		Requires administrator permissions.

		usage: {self.bot.command_prefix}reboot
		"""

		cmd = Popen(["git", "pull"], stdout=PIPE)
		out, _ = cmd.communicate()
		out = out.decode()
		if "+" in out:
			await ctx.send(f"Updated:\n{out}")

		await ctx.send(f"rebooting....")
		await client.Client.logout(self.bot)

	@commands.command(hidden=True, description="Reloads bot cogs")
	@commands.has_permissions(manage_messages=True)
	async def reload(self, ctx, pull=None):
		f"""
		Reloads all bot cogs so updates can be performed while the bot is
		running. Reloading can be from local files OR can pull the most
		recent version of the files from the git repository.

		This reloads files locally by default.

		Examples:
			Reload cogs locally
			{self.bot.command_prefix}reload

			Pull files from github and reload the cogs
			{self.bot.command_prefix}reload pull
			"""

		if pull == "pull":
			cmd = Popen(["git", "pull"], stdout=PIPE)
			out, _ = cmd.communicate()
			if out == b'Already up to date.\n':
				return await ctx.send("I'm already up to date.")
			await ctx.send(f"Pulling files from github...\n{out}")

		await self.load_cogs()
		await ctx.send("Reloaded")

	async def load_cogs(self):
		"""
		Handles loading all cogs in for the bot.
		"""

		cogs = [cog for cog in os.listdir('cogs')
				if os.path.isfile(f"cogs/{cog}")]

		cogs = [cog.replace(".py", "") for cog in cogs]

		for cog in cogs:
			try:
				print(f"Unloading {cog}")
				self.bot.unload_extension(f"cogs.{cog}")
			except commands.errors.ExtensionNotLoaded:
				print(f"Cog {cog} is already unloaded.")

		for cog in cogs:
			try:
				print(f"Loading {cog}...")
				self.bot.load_extension(f"cogs.{cog}")
				print(f"Loaded {cog.split('.')[-1]}")

			except ModuleNotFoundError:
				print(f"Could not find {cog}. Does it exist?")

			except OSError as lib_error:
				print("Opus is probably not installed")
				print(f"{lib_error}")

			except commands.errors.ExtensionAlreadyLoaded:
				print(f"The cog {cog} is already loaded.\n"
					  "Skipping the load process for this cog.")

			except SyntaxError as e:
				print(f"The cog {cog} has a syntax error.")
				traceback.print_tb(e.__traceback__)


def setup(bot):
	bot.add_cog(Admin(bot))
