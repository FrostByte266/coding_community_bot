"""
Commands provided by this cog.

    purge : Deletes messages. Requires permission to manage messages.
    move  : Moves messages between channels. Manage Messages permissions.
"""

import os

from asyncio import sleep
from glob import glob

from discord import Embed, TextChannel, User
from discord.ext import commands


class MessageLoader:
    def __init__(self, search_path):
        self.search_path = search_path

        # Iterate through directory and find all files ending with _message.txt
        for message, path in self.load_names(include_full_paths=True):
            try:
                # Set class variable for the message and read file into it
                with open(path, 'r', encoding='utf-8') as f:
                    self.__dict__[message] = f.read()
            except IOError:
                print(f'Failed to process file: {path}')

    # Allows access to attributes with indexing syntax
    def __getitem__(self, key):
        return self.__dict__[key]

    def load_names(self, include_full_paths=False):
        # Use proper directory separator for host OS
        if os.name == 'nt':
            sep = '\\'
        else:
            sep = '/'

        # Iterate through directory and find all files ending with _message.txt
        for message_file in glob(f'{self.search_path}{sep}*_message.txt'):
            # Strip away path and _message.txt suffix
            absolute_path = os.path.abspath(message_file)
            relative_path = absolute_path.split(sep)[-1]
            message_name = relative_path[:-12]
            if not include_full_paths:
                yield message_name
            else:
                yield (message_name, absolute_path)


class Messages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.messages = MessageLoader('assets/')
        self.message_names = ', '.join(list(self.messages.load_names()))

    async def move_action(self, ctx, count: int, target: TextChannel,
                          copy: bool):
        messages = []
        zero_width_space = u'\u200B'
        async for message in ctx.message.channel.history(limit=count):
            if message.embeds:
                messages.extend(message.embeds)
            else:
                embed = Embed(
                    description=f'{zero_width_space}{message.content}')
                embed.set_author(
                    name=message.author.name,
                    icon_url=message.author.avatar_url)
                embed.timestamp = message.created_at
                messages.append(embed)

            if not copy:
                await message.delete()

        await target.send(f'Moved from {ctx.message.channel.mention}:')

        for embed in reversed(messages):
            await target.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, limit: int, target: User = None):
        """Remove the specified amount of messages"""
        await ctx.message.delete()
        if target is None:
            await ctx.message.channel.purge(limit=limit)
        else:
            await ctx.message.channel.purge(
                limit=limit, check=lambda message: message.author == target)

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.message.delete()
            message = await ctx.send(
                "You are missing the manage messages permission!")
            await sleep(3)
            await message.delete()

    @commands.group(
        name="move", invoke_without_command=True, case_insensitive=True)
    async def move_group(self, ctx):
        if ctx.invoked_subcommand is None:
            message = await ctx.send(
                f"Invalid subcommand passed.  Use {self.bot.command_prefix}help move for available subcommands."
            )
            await sleep(3)
            await message.delete()

    @move_group.command(name="last", aliases=["count", "previous"])
    @commands.has_permissions(manage_messages=True)
    async def last_subcommand(self,
                              ctx,
                              count: int,
                              target: TextChannel,
                              copy: bool = False):
        """Move/copy specified amount of messages to target channel"""
        await ctx.message.delete()
        async with target.typing():
            await self.move_action(ctx, count, target, copy)

    @last_subcommand.error
    async def last_subcommand_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            temp = await ctx.send(
                "Error! Missing one or more of the following arguments: count, target"
            )
            await sleep(3)
            await temp.delete()

    @move_group.command(name="from", aliases=["link"])
    @commands.has_permissions(manage_messages=True)
    async def from_subcommand(self,
                              ctx,
                              message_id: int,
                              target: TextChannel,
                              copy: bool = False):
        """Move/copy all messages up to (and including) a message ID"""
        await ctx.message.delete()
        count = 0
        async for message in ctx.message.channel.history(limit=100):
            count += 1
            if message.id == message_id:
                found = 1
                break

        async with target.typing():
            if found == 1:
                await self.move_action(ctx, count, target, copy)
            else:
                temp = await ctx.send(
                    f"Error! Unable to find message with ID: {message_id}")
                await sleep(3)
                await temp.delete()

    @from_subcommand.error
    async def from_subcommand_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            temp = await ctx.send(
                "Error! Missing one or more of the following arguments: message_id, target"
            )
            await sleep(3)
            await temp.delete()

    @move_group.command(name="range", aliases=["between"])
    @commands.has_permissions(manage_messages=True)
    async def range_subcommand(self,
                               ctx,
                               first_message_id: int,
                               second_message_id: int,
                               target: TextChannel,
                               copy: bool = False):
        """Move/copy all messages between (and including) two message IDs"""
        await ctx.message.delete()
        first_message_found: bool = False
        second_message_found: bool = False
        async for message in ctx.message.channel.history(limit=100):
            if all([first_message_found, second_message_found]):
                break
            if message.id == first_message_id:
                first_message_found = True
            if message.id == second_message_id:
                second_message_found = True

        async with target.typing():
            messages = []
            zero_width_space = u'\u200B'
            first_message_moved: bool = False
            second_message_moved: bool = False
            if all([first_message_found, second_message_found]):
                async for message in ctx.message.channel.history(limit=100):
                    if message.id == first_message_id:
                        first_message_moved = True
                    if message.id == second_message_id:
                        second_message_moved = True
                    if any([first_message_moved, second_message_moved]):
                        if message.embeds:
                            messages.extend(message.embeds)
                        else:
                            embed = Embed(
                                description=
                                f'{zero_width_space}{message.content}')
                            embed.set_author(
                                name=message.author.name,
                                icon_url=message.author.avatar_url)
                            embed.timestamp = message.created_at
                            messages.append(embed)

                        if not copy:
                            await message.delete()
                        if all([first_message_moved, second_message_moved]):
                            break

                await target.send(f'Moved from {ctx.message.channel.mention}:')

                for embed in reversed(messages):
                    await target.send(embed=embed)

            else:
                if first_message_found == False:
                    temp = await ctx.send(
                        f"Error! Unable to find message with ID: {second_message_id}"
                    )
                elif second_message_found == False:
                    temp = await ctx.send(
                        f"Error! Unable to find message with ID: {first_message_id}"
                    )
                else:
                    temp = await ctx.send(
                        f"Error! Unable to find either message with IDs: {first_message_id}, {second_message_id}"
                    )
                await sleep(3)
                await temp.delete()

    @range_subcommand.error
    async def range_subcommand_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            temp = await ctx.send(
                f"Error! Missing one or more of the following arguments: first_message_id, second_message_id, target"
            )
            await sleep(3)
            await temp.delete()

    @commands.command()
    async def message(self, ctx, selection: str):
        if selection == 'list':
            await ctx.send(f'Available messages are: {self.message_names}')
        else:
            # discord.py error handler will catch this if index fails
            await ctx.send(self.messages[selection])

    @message.error
    async def message_error(self, ctx, error):
        if type(ctx.args[-1]) is str:
            await ctx.send(
                f'Choice `{ctx.args[-1]}` is invalid! Available messages are: {self.message_names}'
            )
        else:
            await ctx.send(
                f'No selection specified! Available messages are: {self.message_names}'
            )


def setup(bot):
    bot.add_cog(Messages(bot))
