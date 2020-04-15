"""
Commands provided by this cog.

    verification : Enable or disable the verification setting for the bot.
    verify : User verification. Removes the unverified role if successful.

"""

import json
import datetime

import asyncio

from discord.ext import tasks, commands
from discord.utils import get


class Verification(commands.Cog):
    # Closer the number approaches 1, the more often the word list will be refreshed. Linear

    def __init__(self, bot):
        self.bot = bot
        self.config_full = json.loads(open('assets/config.json').read())
        self.word_list_refresh_rate = 99
        self.word_cache_size = 1000

    @tasks.loop(seconds=86400)
    async def kick_unverified_task(self):
        guild_id_to_monitor = 697292778215833652
        guild = self.bot.get_guild(guild_id_to_monitor)
        guild_members = guild.members
        unverified_role = get(guild.roles, name="Unverified")
        unverified_members = unverified_role.members

        if datetime.today().weekday() != 6:
            for member in unverified_members:
                await member.send(
                    "Automated Sunday Kick Warning: You will be kicked end of day Sunday if you do not "
                    "introduce yourself in #if-you-are-new-click here within the Coding Community server."
                )
            else:
                for member in unverified_members:
                    await member.send(
                        "Automated Sunday Kick Warning: You will be kicked in 5 minutes if you do not "
                        "introduce yourself in #if-you-are-new-click here within the Coding Community server."
                    )

                await asyncio.sleep(300)

                reason = "Automated weekly kick due to not introducing yourself in the #if-you-are-new-click-here channel"
                for member in unverified_members:
                    await guild.kick(member, reason=reason)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def verification(self, ctx, state: bool):
        """Enable or disable the verification system"""
        config = self.config_full[str(ctx.message.guild.id)]
        if state is True and config["verification_role"] is None:
            role = await ctx.message.guild.create_role(name="Unverified")
            config.update(verification_role=role.id)
            json.dump(self.config_full, open('assets/config.json',
                                             'w'), indent=2, separators=(',', ': '))
        elif state is False and config["verification_role"] is not None:
            role = get(ctx.message.guild.roles, id=config["verification_role"])
            await role.delete()
            config.update(verification_role=None)
            json.dump(self.config_full, open('assets/config.json',
                                             'w'), indent=2, separators=(',', ': '))


def setup(bot):
    bot.add_cog(Verification(bot))
