import json
import logging
import os
import re
import traceback

from datetime import datetime, timedelta

import asyncio

from discord import Embed, Message
from discord.ext import commands, tasks
from discord.errors import Forbidden
from discord.utils import get


class CodingBot:
    """The main class of the bot

    :param config_file: The path to the config file
    :type config_file: str
    """
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
        """Fetches a value from the environment and prompts if missing

        :param env_key: The key of the environment variable
        :type env_key: str
        :param prompt: The prompt to give if the key is missing
        :type prompt: str
        :return: The environment variable value or user input
        :rtype: str
        """
        env_var = os.environ.get(env_key, None)
        return env_var if env_var is not None else input(f'Please provide the {prompt}: ')

    def load_config_and_fetch_token(self, config_file):
        """Loads the bot config for use

        :param config_file: The path to the bot's config file
        :type config_file: str
        :return: Tuple of the initial config as a dict and the bot's token
        :rtype: Tuple[dict, str]
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
        """Reloads the config file

        :param new_config: The config to overwrite the current config
        :type new_config: dict
        :param write: Defines if the file should be updated on disk, defaults to True
        :type write: bool, optional
        """
        self.config = new_config
        if write:
            json.dump(new_config, open(self.config_file_path, 'w'),
                      indent=2, separators=(',', ': '))
            
    def start_logging(self, log="discord.log"):
        """Sets up the bot log

        :param log: the logfile to use, defaults to "discord.log"
        :type log: str, optional
        """
        # Rotate logs
        old_log_path = f'{log}.old'
        if os.path.exists(old_log_path):
            os.remove(old_log_path)
        if os.path.exists(log):
            os.rename(log, old_log_path)

        self.bot.logger = logging.getLogger('discord')
        self.bot.logger.setLevel(logging.WARNING)
        self.bot.handler = logging.FileHandler(filename=log,
                                        encoding='utf-8', mode='w')
        self.bot.handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:'
                                                '%(name)s: %(message)s'))
        self.bot.logger.addHandler(self.bot.handler)
    
    def stop_logging(self):
        """Closes the log file"""
        self.bot.handler.close()

    def load_cogs(self):
        """Loads all cogs in the 'cogs' directory"""
        for file in os.listdir('./cogs'):
            if file.endswith('.py'):
                try:
                    self.bot.load_extension(f'cogs.{file[:-3]}')
                except Exception as e:
                    print(f"Failed to load cog {file}")
                    print(f"Error:\n{e}")

    def run_bot(self):
        """Runs the bot"""
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.bot.start(self.bot_token))
        except Exception as e:
            print("Error", e)
        print("Restarting...")

    def attachments_are_images(self, message):
        """Checks if the attachment of a message is an image

        :param message: The message to check
        :type message: discord.Message
        :return: A bool representing if the attachment is an image
        :rtype: bool
        """
        attachments = message.attachments
        permitted_types = ('png', 'jpg', 'jpeg', 'gif', 'bmp')
        file_extensions = (file.filename.split('.')[-1] for file in attachments)

        attachments_permissible =  (extension in permitted_types for extension in file_extensions) 
        return all(attachments_permissible)

    def can_upload_files(self, member):
        """Checks if a member is able to upload a file

        :param member: The member to check
        :type member: discord.Member
        :return: A bool representing if the member can attach files
        :rtype: bool
        """
        min_age_images = timedelta(days=2)
        min_age_files = timedelta(days=30)

        member_age = datetime.utcnow() - member.joined_at
        print(member_age)

        if member_age < min_age_images:
            return False
        elif member_age > min_age_images and member_age < min_age_files:
            return 'IMAGE_ONLY'
        else:
            return True
            
    def build_bot(self):
        """Builds the discord bot object

        :return: The bot to be used
        :rtype: discord.ext.commands.Bot
        """
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
            bot.logger.info('Bot started')

            # Check if there are any new servers the bot does not have configs for
            [setup_guild_config(guild) for guild in bot.guilds if str(guild.id) not in self.config]


        @bot.event
        async def on_message(message):
            is_bot = message.author == bot.user
            is_webhook = message.webhook_id is not None
            not_guild = message.guild is None
            if any((is_bot, is_webhook, not_guild, message.content.startswith('!d bump'))):
                return None


            config = self.config[str(message.guild.id)]
            verification_enabled = True if config["verification_role"] is not None else False
            unverified_role = get(message.author.guild.roles, name="Unverified")

            if all((str(message.channel) == 'if-you-are-new-click-here', message.content is not None)):
                content = re.sub("^-|[\.\:\;\,]", " ", message.content, flags=re.UNICODE)
                word_group = content.split()

                ignored_roles = ('@everyone', 'Admin', 'Spartan Mod', 'Moderator', 'Owner', 'Staff',
                                 'Merit Badge (lvl - M)',
                                 'Merit Badge (lvl - A)',
                                 'Merit Badge (lvl - O)', 'BOT', 'little fox familiar')

                roles = {role.name.lower(): role for role in message.guild.roles if role.name not in ignored_roles}

                current_category = set()
                categorized_roles = dict()
                desired_categories = ('Experience', 'Languages')
                for role in roles.values():
                    if not role.name.startswith('-'):
                        # Role is not a category, add it to the current category
                        current_category.add(role)
                    else:
                        # Role is a category, add all roles under it, and reset
                        role_name = role.name[1:]
                        if role_name in desired_categories:
                            # If the category isn't ignored, add it to the dict, otherwise discard it
                            categorized_roles[role_name] = current_category
                        current_category = set()

                # Some aliases added to catch for spelling errors
                alias = (('js', roles['javascript']),
                         ('cpp', roles['c++']),
                         ('c', roles['clang']),
                         ('intermediate', roles['novice']),
                         ('begginer', roles['beginner']),
                         ('beginer', roles['beginner']),
                         ('begener', roles['beginner']))

                for element in alias:
                    roles[element[0]] = element[1]


                detected_roles = set((roles.get(word.lower(), 0) for word in word_group if roles.get(word.lower(), 0) != 0))

                if all((categorized_roles[category] & detected_roles for category in categorized_roles.keys())):
                    filtered_roles = tuple(x for x in detected_roles if not x.name.startswith('-'))
                    await message.author.add_roles(*filtered_roles)
                    newline = '\n'
                    await message.author.send(
                        f'Hello, based on your introduction, you have automatically been assigned the following roles: \n'
                        f'{newline.join(role.name for role in filtered_roles)}, \n'
                        '\nIf you believe you are missing some roles or have received roles that do not apply to you, '
                        'please feel free to contact the moderation team'
                    )
                    if verification_enabled:
                        await message.author.remove_roles(unverified_role)
                elif unverified_role not in message.author.roles and message.content.startswith('-'):
                    roles_after_removal = set(message.author.roles) - detected_roles
                    meets_minimum_languages =  len(categorized_roles['Languages'] & roles_after_removal) > 2
                    has_all_categories = all((categorized_roles[category] & roles_after_removal for category in categorized_roles.keys()))
                    if all((meets_minimum_languages, has_all_categories)):
                        await message.author.remove_roles(*detected_roles)
                else:
                    await message.author.send(
                        'You must have at least one experience level role and one skill role in your introduction. '
                        'Please review the #readme channel for an example of a valid introduction.'
                    )
            elif all((verification_enabled, str(message.channel) != 'if-you-are-new-click-here', unverified_role in message.author.roles)):
                await message.author.send("Before you can send messages you need to introduce yourself in #if-you-are-new-click-here."
                                          " Please state any programming languages you have used, as well as whether you are a"
                                          "Beginner, Novice, Advanced, or Professional. You can review earlier introductions in "
                                          "the #if-you-are-new-click-here channel for examples.")
                await message.delete()
            elif message.attachments:
                upload_eligibility = self.can_upload_files(message.author)
                print(upload_eligibility)
                print(self.attachments_are_images(message))
                if upload_eligibility == 'IMAGE_ONLY' and not self.attachments_are_images(message):
                    await message.delete()
                    await message.channel.send('Sorry, you do not yet meet the requirements to upload non image file types')
                elif not upload_eligibility:
                    await message.delete()
                    await message.channel.send('Sorry, you do not yet meet the requirements to upload files/images. '
                                                'If you need to share images, please use an image sharing service such as Imgur')
                    
            await bot.process_commands(message)

        @bot.event
        async def on_error(error, *args, **kwargs):
            bot.logger.exception(f'Uncaught exception in: {error}', exc_info=True)

        @bot.event
        async def on_command_error(ctx, error):
            bot.logger.exception(f'Uncaught exception in: {ctx.command}', exc_info=error)
            

        @bot.event
        async def on_member_join(member):
            config = self.config[str(member.guild.id)]
            verification_enabled = True if config["verification_role"] is not None else False
            if all((verification_enabled, not member.bot)):
                role = get(member.guild.roles, id=config["verification_role"])
                await member.add_roles(role)

            try:
                await member.send(self.welcome_message)
            except Forbidden:
                pass

            # Prepare welcome embed
            embed = Embed(
                color=0x9370DB,
                description=f'You are member {len(list(member.guild.members))} 🎉'
            )
            embed.set_thumbnail(url=member.avatar_url)
            embed.set_author(name=member.name, icon_url=member.avatar_url)
            embed.set_footer(text=member.guild, icon_url=member.guild.icon_url)
            embed.timestamp = datetime.utcnow()

            # Get the server message channel and send welcome message there
            channel = bot.get_channel(id=member.guild.system_channel.id)

            # Get the server rule channel
            rule_channel = get(member.guild.text_channels, name='readme')

            # Get the server intro channel
            intro_channel = get(member.guild.text_channels, name='if-you-are-new-click-here')

            channel_welcome_message = f' Welcome to our server {member.mention}.' \
                                      f' Take some time to review the {rule_channel.mention},' \
                                      f' this contains the server rules, culture, and customs.' \
                                      f' Also, don\'t forget to introduce yourself in' \
                                      f' the {intro_channel.mention} channel.'

            await channel.send(channel_welcome_message, embed=embed)

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
