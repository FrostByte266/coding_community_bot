"""
All commands in this cog are assumed to require administrator level permissions
to run. These commands are intended to make administration of the bot itself
easier.

Commands provided by this Cog

    - logging  : Changes the log level of the bot
    - poweroff : Turns the bot off
    - reboot   : Reboots the bot and pulls changes from github
    - reload   : Reloads the bot configuration from local files OR pulls from
                 github and then reloads.

"""

import os
import functools
import traceback

from datetime import datetime
from io import StringIO

from discord.ext import commands
from discord import client, Forbidden, Role, Permissions, File
from discord.utils import get
from subprocess import Popen, PIPE
from utils import admin_utils


class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        admin_utils.setup_logging(self.bot)

    @commands.command(hidden=True, description="Sets bot logging level")
    async def logging(self, ctx, level):
        """
        Sets the logging level on the bot. Valid levels are, from most verbose
        to least:
            debug
            info
            warning
            error
            critical
        """

        valid_levels = ['debug', 'info', 'warning', 'error', 'debug']
        level = level.lower()

        if level in valid_levels:
            await admin_utils.set_logging_level(self.bot, level.upper())
            await ctx.send(f"Logging level set to {level}")
        else:
            await ctx.send("Invalid logging level specified.")

    @commands.command(pass_context=True, hidden=True, description="replaces old pre-patch role with with discord team mute respecting patched role")
    @commands.has_permissions(administrator=True)
    async def role_refresh(self, ctx, role: Role):
        affected_members = role.members

        new_role = await ctx.guild.create_role(
            name=role.name,
            permissions=role.permissions,
            mentionable=role.mentionable,
            color=role.color,
            hoist=role.hoist,
        )
        await new_role.edit(position=role.position)
        await ctx.send('Role refresh initiated, this may take a while...')

        # Remove old role from members before deleting
        for member in affected_members:
            await member.remove_roles(role, reason='Removal of old role for role refresh')

        # Delete the old role, and add the new role back
        await role.delete(reason='Performing role refresh')
        for member in affected_members:
            await member.add_roles(new_role, reason='Adding refreshed role')

        await ctx.send('Role refresh complete :thumbsup:')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def list_unverified(self, ctx):
        unverfied_role = get(ctx.guild.roles, name='Unverified')
        list_of_members = [f'{member.name} (ID: {member.id})' for member in unverfied_role.members]
        newline_separated_list = '\n'.join(sorted(list_of_members))
        length_of_list = len(newline_separated_list)
        if length_of_list > 2000:
            buffer = StringIO()
            buffer.write(newline_separated_list)
            buffer.seek(0)
            timestamp = datetime.now().strftime('%m-%d-%Y_%H%M')
            upload = File(buffer, filename=f'unverified_list_{timestamp}.txt')
            await ctx.send('List exceeds message character limit, please refer to the attached file', file=upload)
        elif length_of_list == 0:
            await ctx.send('No unverified members!')
        else:
            await ctx.send(newline_separated_list)

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
    @commands.has_permissions(manage_messages=True)
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
            out = out.decode('utf-8')
            if out == 'Already up to date.\n':
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
