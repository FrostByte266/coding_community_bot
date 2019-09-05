import aiohttp
import json
import random

from discord.ext import commands

class XkcdFetcher(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.prefix = self.bot.command_prefix

	async def get_quote(self, url):
		async with aiohttp.ClientSession() as session:
			html = await self.fetch(session, url)
			return html


	async def fetch(self, session, url):
		async with session.get(url) as html:
			return await html.text()


	@commands.command(description="gets an XKCD webcomic")
	async def xkcd(self, ctx):
		"""
		Gets an XKCD comic. By default, will grab a random comic.

		Examples:
			Get a random webcomic
			{self.prefix}xckd

			Get comic number 404
			{self.prefix}xkcd 404
		"""

		command = ctx.message.content.split(" ")
		command = command[1:]

		latest = await self.get_quote("https://xkcd.com/info.0.json")
		latest = json.loads(latest)

		if command:
			try:
				xkcd_num = int(command[0])
				if xkcd_num > latest["num"]:
					xkcd_num = latest["num"]
				elif xkcd_num < 1:
					xkcd_num = 1
			except ValueError:
				await ctx.send("I don't know what to do with that. I'll give "
							   "you a random comic for now. If you're "
							   "unsure of how to use this command, run\n"
							   f"```{self.prefix}help xkcd```")
				xkcd_num = random.randint(1, latest["num"])
		else:
			xkcd_num = random.randint(1, latest["num"])

		await ctx.send(f"https://xkcd.com/{xkcd_num}")

def setup(bot):
	bot.add_cog(XkcdFetcher(bot))
