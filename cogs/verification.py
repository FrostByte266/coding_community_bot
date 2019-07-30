"""
Commands provided by this cog.

    verification : Enable or disable the verification setting for the bot.
    verify : User verification. Removes the unverified role if successful.

"""

import aiohttp
import json
from random import choice, choices, randint, sample

from discord import File
from discord.ext import commands
from discord.utils import get


class Verification(commands.Cog):
	# Closer the number approaches 1, the more often the word list will be refreshed. Linear

	def __init__(self, bot):
		self.bot = bot
		self.config_full = json.loads(open('assets/config.json').read())
		self.word_list_refresh_rate = 99
		self.word_cache_size = 1000

	@commands.command()
	@commands.has_permissions(manage_guild=True)
	async def verification(self, ctx, state: bool):
		"""Enable or disable the verification system"""
		config = self.config_full[str(ctx.message.guild.id)]
		if state is True and config["verification_role"] is None:
			role = await ctx.message.guild.create_role(name="Unverified")
			config.update(verification_role=role.id)
			json.dump(self.config_full, open('assets/config.json', 'w'), indent=2, separators=(',', ': '))
		elif state is False and config["verification_role"] is not None:
			role = get(ctx.message.guild.roles, id=config["verification_role"])
			await role.delete()
			config.update(verification_role=None)
			json.dump(self.config_full, open('assets/config.json', 'w'), indent=2, separators=(',', ': '))

def setup(bot):
	bot.add_cog(Verification(bot))
