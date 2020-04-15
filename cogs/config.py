"""
Commands provided by this cog.

    reporting : Enables or disables the reporting feature

"""

import json

from discord.utils import get
from discord.ext import commands


class Config(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config_full = json.loads(open('assets/config.json').read())

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def reporting(self, ctx, state: bool):
        """Enable or disable report receipts being sent in a channel"""
        config = self.config_full[str(ctx.message.guild.id)]
        if state is True and config["reporting_channel"] is None:
            channel = await ctx.message.guild.create_text_channel(name="Reporting")
            config.update(reporting_channel=channel.id)
            json.dump(self.config_full, open('assets/config.json',
                                             'w'), indent=2, separators=(',', ': '))
        elif state is False and config["reporting_channel"] is not None:
            channel = get(ctx.message.guild.text_channels,
                          id=config["reporting_channel"])
            await channel.delete()
            config.update(reporting_channel=None)
            json.dump(self.config_full, open('assets/config.json',
                                             'w'), indent=2, separators=(',', ': '))


def setup(bot):
    bot.add_cog(Config(bot))
