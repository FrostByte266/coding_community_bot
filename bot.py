from datetime import datetime
import json
import os
import re

import asyncio

from discord import Embed, Message
from discord.ext import commands, tasks
from discord.utils import get


class CodingBot:

    def __init__(self, config_file):
        self.config_file_path = config_file
        self.config, self.bot_token = self.load_config_and_fetch_token(
            config_file)
        self.bot = self.build_bot()
        self.bot.boot_time = datetime.now()
        self.load_cogs()
        self.url_regex = re.compile("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
        with open('assets/welcome_message.txt') as f:
            self.welcome_message = f.read()
        self.empty_config = {
            'verification_role': None,
            'reporting_channel': None,
            'reddit_config': {},
            'reports': {}
        }

    def get_initial_config_value(self, env_key, prompt):
        env_var = os.environ.get(env_key, None)
        return env_var if env_var is not None else input(f'Please provide the {prompt}: ')

    def load_config_and_fetch_token(self, config_file):
        """
        Loads bot configuration for use.
        """
        token = None
        try:
            # Attempt to fetch the token from config.json
            config = json.loads(open(config_file, 'r').read())
            token = config['token']
            return (config, token)
        except FileNotFoundError:
            # If config.json does not exist, it must be the first time starting the
            # bot, run through configuration
            # If running from a docker container, fetch the token through an
            # environment variable, otherwise, prompt the user to enter it
            prefix = self.get_initial_config_value('BOT_PREFIX', 'prefix for the bot')
            token = self.get_initial_config_value('BOT_TOKEN', 'bot API token')
            client_id = self.get_initial_config_value('REDDIT_CLIENT_ID', 'Reddit API client ID')
            client_secret = self.get_initial_config_value('REDDIT_CLIENT_SECRET', 'Reddit API client secret')
            reddit_username = self.get_initial_config_value('REDDIT_BOT_USER', 'username for the Reddit bot')
            reddit_pass = self.get_initial_config_value('REDDIT_BOT_PASSWORD', 'password for the Reddit bot')


            initial_config = {
                'token': token,
                'prefix': prefix,
                'reddit_config': {
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'username': reddit_username,
                    'password': reddit_pass
                },
                'reddit_enabled': []
            }

            json.dump(initial_config, open(config_file, 'w'),
                      indent=2, separators=(',', ': '))

            os.makedirs('./assets/network_charts', exist_ok=True)
            os.makedirs('./assets/role_charts', exist_ok=True)

            return (initial_config, token)

    def refresh_config(self, new_config, write=True):
        self.config = new_config
        if write:
            json.dump(new_config, open(self.config_file_path, 'w'),
                      indent=2, separators=(',', ': '))

    def load_cogs(self):
        for file in os.listdir('./cogs'):
            if file.endswith('.py'):
                try:
                    self.bot.load_extension(f'cogs.{file[:-3]}')
                except Exception as e:
                    print(f"Failed to load cog {file}")
                    print(f"Error:\n{e}")

    def run_bot(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.bot.start(self.bot_token))
        except Exception as e:
            print("Error", e)
        print("Restarting...")

    async def category_check(self, message):
        if 'resources' in message.channel.category.name.lower() and not self.url_regex.search(message.content):
            failMessage = f"**Message Removed**\nSorry but your message in #{message.channel.name} does not contain a link to your external reference. If this was a mistake please try resubmitting your message with the link. If this was intended as a conversational message please re-send it in General or Chill-Chat."
            await message.delete()
            await message.author.send(failMessage)
            

    def build_bot(self):
        bot = commands.Bot(
            command_prefix=self.config['prefix'],
            case_insensitive=True)

        def setup_guild_config(guild):
            # Add empty config to JSON for any server that is missing
            self.config[str(guild.id)] = self.empty_config
            # Save to config file
            self.refresh_config(self.config)

        @bot.event
        async def on_ready():
            print("Ready")

            # Check if there are any new servers the bot does not have configs for
            [setup_guild_config(guild) for guild in bot.guilds if str(guild.id) not in self.config]


        @bot.event
        async def on_message(message):
            is_bot = message.author == bot.user
            not_guild = message.guild is None
            if any((is_bot, not_guild)):
                return None

            await self.category_check(message)

            config = self.config[str(message.guild.id)]
            verification_enabled = True if config["verification_role"] is not None else False
            unverified_role = get(
                message.author.guild.roles, name="Unverified")

            if all((str(message.channel) == 'if-you-are-new-click-here', message.content is not None)):
                content = re.sub("[\.\:\;\,]", " ", message.content, flags=re.UNICODE)
                word_group = [x.strip() for x in content.split()]

                ignored_roles = ['@everyone', 'Admin', 'Spartan Mod', 'Moderator', 'Owner', 'Staff',
                                 'Merit Badge (lvl - M)',
                                 'Merit Badge (lvl - A)',
                                 'Merit Badge (lvl - O)', 'BOT', 'little fox familiar']

                roles = {role.name.lower(
                ): role for role in message.guild.roles if role.name not in ignored_roles}
                member_roles = [roles.get(
                    word.lower(), 0) for word in word_group if roles.get(word.lower(), 0) != 0]
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
            elif all((verification_enabled, str(message.channel) != 'if-you-are-new-click-here', unverified_role in message.author.roles)):
                await message.author.send("Before you can send messages you need to introduce yourself in #if-you-are-new-click-here."
                                          " Please state any programming languages you have used, as well as whether you are a"
                                          "Beginner, Novice, Advanced, or Professional. You can review earlier introductions in "
                                          "the #if-you-are-new-click-here channel for examples.")
                await message.delete()
            await bot.process_commands(message)

        @bot.event
        async def on_member_join(member):
            config = self.config[str(member.guild.id)]
            verification_enabled = True if config["verification_role"] is not None else False
            if all((verification_enabled, not member.bot)):
                role = get(member.guild.roles, id=config["verification_role"])
                await member.add_roles(role)

            await member.send(self.welcome_message)

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
            embed = Embed(
                color=0x9370DB, description=f'Goodbye! Thank you for spending time with us!')
            embed.set_thumbnail(url=member.avatar_url)
            embed.set_author(name=member.name, icon_url=member.avatar_url)
            embed.set_footer(text=member.guild, icon_url=member.guild.icon_url)
            embed.timestamp = datetime.utcnow()

            # Get the server message channel and send goodbye message there
            channel = bot.get_channel(id=member.guild.system_channel.id)

            await channel.send(embed=embed)

        @bot.event
        async def on_guild_join(guild):
            # Create configuration dict to store in JSON
            self.config[str(guild.id)] = self.empty_config
            # Save to config file
            self.refresh_config(self.config)

        @bot.event
        async def on_guild_remove(guild):
            self.config.pop(str(guild.id))
            self.refresh_config(self.config)

        return bot
