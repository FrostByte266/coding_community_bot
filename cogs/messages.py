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
        # Use proper directory separator for host OS
        if os.name == 'nt':
            sep = '\\'
        else:
            sep = '/'

        # Iterate through directory and find all files ending with _message.txt
        for message_file in glob(f'{search_path}{sep}*_message.txt'):
            # Strip away path and _message.txt suffix
            absolute_path = os.path.abspath(message_file).split(sep)[-1]
            message_name = absolute_path[:-12]
            try:
                # Set class variable for the message and read file into it
                with open(message_file, 'r', encoding='utf-8') as f:
                    self.__dict__[message_name] = f.read()
            except IOError:
                print(f'Failed to process file: {message_file}')
            

class Messages(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.messages = MessageLoader('assets/')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, limit: int, target: User = None):
        """Remove the specified amount of messages"""
        await ctx.message.delete()
        if target is None:
            await ctx.message.channel.purge(limit=limit)
        else:
            await ctx.message.channel.purge(limit=limit, check=lambda message: message.author == target)

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.message.delete()
            message = await ctx.send("You are missing the manage messages permission!")
            await sleep(3)
            await message.delete()

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def move(self, ctx, count: int, target: TextChannel, copy: bool = False):
        """Move/copy specified amount of messages to target channel"""
        async with target.typing():
            await ctx.message.delete()
            messages = []
            zero_width_space = u'\u200B'
            async for message in ctx.message.channel.history(limit=count):
                if any([emb.description.startswith(zero_width_space) for emb in message.embeds]):
                    messages.extend(message.embeds)
                else:
                    embed = Embed(description=f'{zero_width_space}{message.content}')
                    embed.set_author(name=message.author.name,
                                    icon_url=message.author.avatar_url)
                    embed.timestamp = message.created_at
                    messages.append(embed)
                    
                if not copy:
                    await message.delete()

            await target.send(f'Moved from {ctx.message.channel.mention}:')

            for embed in reversed(messages):
                await target.send(embed=embed)

    @move.error
    async def move_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            temp = await ctx.send("Error! Missing one or more of the following arguments: count, target")
            await sleep(3)
            await temp.delete()

    @commands.command()
    async def courtesy(self, ctx):
        await ctx.send(self.messages.courtesy)

    @commands.command()
    async def patience(self, ctx):
        await ctx.send(self.messages.patience)

    @commands.command()
    async def question(self, ctx):
        await ctx.send(self.messages.question)



def setup(bot):
    bot.add_cog(Messages(bot))
