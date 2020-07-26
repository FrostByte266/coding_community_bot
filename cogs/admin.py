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

import asyncio
import discord
import functools
import os
import traceback

from datetime import datetime, timedelta
from io import StringIO


from discord.ext import commands
from discord import client, Forbidden, Role, Permissions, File, PermissionOverwrite

from discord.utils import get
from subprocess import Popen, PIPE
from utils import admin_utils


def ident_string(discord_object):
    root_module = discord_object.__module__.split('.')[0]
    assert root_module == 'discord', f'Ident string called on non discord object'
    return f'{discord_object.name} (ID: {discord_object.id})'

def to_file(contents, filename='message.txt'):
    return discord.File(StringIO(contents), filename=filename)

class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

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

    def slow_channels(self, ctx, seconds):
        for channel in ctx.guild.channels:
            channel.slowmode_delay(seconds)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def alert_level(self, ctx, alert_status):
        roles_present = (role.name.lower() for role in ctx.author.roles)

        alert_patterns = {'green':[0],
                          'alpha':[30],
                          'beta':[120],
                          'gamma':[300]}

        if alert_status not in ['green','alpha','beta','gamma']:
            ctx.send('given alert status is available')
        elif 'moderator' in roles_present:
            alert_level = alert_patterns['alpha']
            self.slow_channels(ctx,alert_level[0])

        elif 'spartan mod' in roles_present:
            alert_status = 'beta' if alert_status == 'gamma' else alert_status
            alert_level = alert_patterns[alert_status]
            self.slow_channels(ctx, alert_level[0])
        else:
            alert_level = alert_patterns[alert_status]
            self.slow_channels(ctx, alert_level[0])


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
        self.bot.logger.info(f'Beginning role refresh for role {ident_string(role)}, initiated by {ident_string(ctx.author)} for {ident_string(ctx.guild)}')

        # Remove old role from members before deleting
        for member in affected_members:
            await member.remove_roles(role, reason='Removal of old role for role refresh')

        # Delete the old role, and add the new role back
        await role.delete(reason='Performing role refresh')
        for member in affected_members:
            await member.add_roles(new_role, reason='Adding refreshed role')

        await ctx.send('Role refresh complete :thumbsup:')
        self.bot.logger.info(f'Role refresh for role {ident_string(role)}, initiated by {ident_string(ctx.author)} for {ident_string(ctx.guild)} completed')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def add_unverified(self, ctx):
        default_role = '@everyone'
        unverified_role = get(ctx.guild.roles, name="Unverified")
        for member in ctx.guild.members:
            member_roles = [role.name for role in member.roles if role.name != default_role]
            if len(member_roles) == 0:
                await member.add_roles(unverified_role)
                self.bot.logger.info(f'Added Unverified to {ident_string(member)} in {ident_string(ctx.guild)}')


    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick_unverified(self, ctx):
        self.bot.logger.info(f'Unverified kick started by {ident_string(ctx.author)} for {ident_string(ctx.guild)}')
        default_role = '@everyone'
        unverified_role = get(ctx.guild.roles, name="Unverified")
        count = 0

        unverified_members = tuple(member for member in unverified_role.members if len(member.roles) < 3)
        fix_members = set(member for member in unverified_role.members if len(member.roles) > 2)

        for member in fix_members:
            await ctx.send(f'{member.name} has additional roles. Please remove unverified from this user.')

        unverified_announcements = get(ctx.guild.text_channels, name='unverified-announcements')
        intro_channel = get(ctx.guild.text_channels, name='if-you-are-new-click-here')
        marker = await intro_channel.fetch_message(intro_channel.last_message_id)
        kick_eligible_members = set(member for member in unverified_members if (datetime.now() - member.joined_at).days >= 7) - fix_members

        await unverified_announcements.send(f'{unverified_role.mention} **WARNING**: '
                                            f'In 5 minutes, members who have joined '
                                            f'7 or more days ago will be kicked in 5 minutes '
                                            f'unless they introduce themselves in {intro_channel.mention}. '
                                            f'To avoid getting kicked, you must introduce yourself in the '
                                            f'{intro_channel.mention} channel within the next 5 minutes.'
        )

        warning_message = '**WARNING**: In 5 minutes, you will be kicked from ' \
                        'Coding Community for failure to introduce yourself ' \
                        'in #if-you-are-new-click-here. To avoid being kicked, ' \
                        'introduce yourself in the aformentioned channel within 5 minutes.'

        for member in kick_eligible_members:
            try:
                await member.send(warning_message)
            except discord.errors.Forbidden:
                continue

        await asyncio.sleep(900)

        intro_authors = set(message.author for message in await intro_channel.history(after=marker).flatten())

        final_kick_list = kick_eligible_members - intro_authors
        kick_reason = 'Failure to introduce within 7 day period'
        rejoin_invitation = 'Uh-oh! It looks like you were kicked for ' \
                            'not introducing yourself. If at any point in ' \
                            'the future you\'d like to rejoin then you may use' \
                            'this link: https://discord.gg/gneEsMS'

        kicked_member_names = (str(member) for member in final_kick_list)
        failed_dms = []
        for member in final_kick_list:
            try:
                await member.send(rejoin_invitation)
            except discord.errors.Forbidden:
                failed_dms.append(member.name)

            await member.kick(reason=kick_reason)
        

        current_datetime = datetime.now().strftime('%m-%d-%Y_%H%M')
        newline = '\n'
        report = f'{ctx.guild} Unverified Kick Report - {current_datetime}{newline}' \
                f'Kicked a total of {len(final_kick_list)} member(s):{newline}' \
                f'{newline.join(kicked_member_names)}{newline}' \
                f'Due to DM privacy settings, {len(failed_dms)} member(s) ' \
                f'were unable to receive re-invtes via DM, these members are:{newline}' \
                f'{newline.join(failed_dms)}'

        await ctx.send(f'Kicked {len(final_kick_list)} members with {len(failed_dms)} failed re-invite DMs. '
                        f'Full report attached:',
                        file=to_file(report, filename=f'kick-report-{current_datetime}.txt')
                    )


    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn_unverified(self, ctx):
        default_role = '@everyone'
        unverified_role = get(ctx.guild.roles, name="Unverified")
        intro_channel = get(ctx.guild.text_channels, name="if-you-are-new-click-here")
        channel = get(ctx.guild.text_channels, name='unverified-announcements')
        count = len(unverified_role.members)

        await channel.send(f'{unverified_role.mention} '
                           f'Please introduce yourself in {intro_channel.mention}. '
                           f'The Moderation Team regularly kicks Unverified members that have been on'
                           f' the server more then 7 days. Please notify @Moderator if the Unverified role '
                           f'is not automatically removed within 5 minutes of your introduction within '
                           f'{intro_channel.mention}'
                           )

        unverified_members = set(unverified_role.members)

        report_message = f'The following is a list of all {len(unverified_members)} members' \
                         f' that currently have the unverified role:'
        report_list = '\n'.join(member.name for member in unverified_members)
        report_full = f'{report_message} \n {report_list}'

        current_datetime = datetime.now().strftime('%m-%d-%Y_%H%M')
        await ctx.send(report_message,
                       file=to_file(report_full, filename=f'unverified-report-{current_datetime}.txt')
                       )

        fix_members = set(member for member in unverified_role.members if len(member.roles) > 2)

        report_message = f'The following attached list of {len(fix_members)} members are those ' \
                 f'that may need unverified removed due to them having roles assigned, ' \
                 f'please check and fix if necessary:'
        report_list = '\n'.join(member.name for member in fix_members)
        report_full = f'{report_message} \n {report_list}'

        current_datetime = datetime.now().strftime('%m-%d-%Y_%H%M')
        await ctx.send(report_message,
                       file=to_file(report_full, filename=f'fix-report-{current_datetime}.txt')
                       )

        dm_count = 0
        no_dm_group = []
        for member in unverified_members - fix_members:
            joined_delta = datetime.now() - member.joined_at
            try:
                if joined_delta.days > 7:
                    await member.send('Please introduce yourself in #if-you-are-new-click-here. '
                                      'The Moderation Team regularly kicks Unverified members that have been on'
                                      'the server more then 7 days, a category which you fall into. Please notify @Moderator if the Unverified role '
                                      'is not automatically removed within 5 minutes of your introduction within '
                                      '#if-you-are-new-click-here')
                else:
                    await member.send('Please introduce yourself in #if-you-are-new-click-here. '
                                      'The Moderation Team regularly kicks Unverified members that have been on'
                                      'the server more then 7 days. Please notify @Moderator if the Unverified role '
                                      'is not automatically removed within 5 minutes of your introduction within '
                                      '#if-you-are-new-click-here')
                self.bot.logger.info(f'Warning message sent to {ident_string(member)} for guild {ident_string(ctx.guild)}')
                dm_count += 1
            except discord.errors.Forbidden:
                # Unable to DM user, move on to next user
                no_dm_group.append(member.name)
                continue

        report_message = f'Sent {dm_count} warnings via DM. The following' \
                         f' list were people unable to be DM\'d:'
        report_list = '\n'.join(no_dm_group)
        report_full = f'{report_message} \n {report_list}'

        current_datetime = datetime.now().strftime('%m-%d-%Y_%H%M')
        await ctx.send(report_message,
                       file=to_file(report_full, filename=f'no-dm-report-{current_datetime}.txt')
                       )


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def block_unverified(self, ctx):
        self.bot.logger.into(f'Blocking unverified in {ident_string(ctx.guild)}, initiated by {ident_string(ctx.author)}')
        ignored_categories = ['getting started', 'purgatory']
        unverfied_role =  get(ctx.guild.roles, name="Unverified")
        
        for channel in ctx.guild.channels:
            existing_overwrites = dict(channel.overwrites)
            write_new_pemissions = False
            category = channel.category.name.lower() if channel.category is not None else 'no-category'
            if category == 'purgatory':
                overwrite_to_apply = PermissionOverwrite(send_messages=False, read_message_history=True, read_messages=True)
                write_new_pemissions = True
            elif category not in ignored_categories:
                overwrite_to_apply = PermissionOverwrite(send_messages=False, read_messages=False)
                write_new_pemissions = True
            
            if write_new_pemissions:
                new_overwrites = {
                    unverfied_role: overwrite_to_apply
                }
                merged_overwrites = {**existing_overwrites, **new_overwrites}
                await channel.edit(overwrites=merged_overwrites, reason='Denying Unverified roles')
                self.bot.logger.info(f'Channel permissions for unverified updated in #{ident_string(channel)} ({ident_string(ctx.guild)})')



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
        self.bot.logger.info(f'Bot shutdown (command invoked by {ident_string(ctx.author)})')
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
        updating = '+' in out
        if updating:
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

        updating = pull == 'pull'
        self.bot.logger.info(f'Bot reboot (pull={"yes" if updating else "no"})(command invoked by {ident_string(ctx.author)})')
        if updating:
            cmd = Popen(["git", "pull"], stdout=PIPE)
            out, _ = cmd.communicate()
            out = out.decode('utf-8')
            if out == 'Already up to date.\n':
                return await ctx.send("I'm already up to date.")
            await ctx.send(f"Pulling files from github...\n{out}")
            self.bot.logger.info(f'Pulled update:\n {out}')

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
