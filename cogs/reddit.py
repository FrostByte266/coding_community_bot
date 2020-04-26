from discord.ext import commands, tasks
from discord import PermissionOverwrite, client
from random import sample

import json
import praw
from itertools import chain


class Reddit(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.reddit = await self.reddit_bot()
        self.config_path = 'assets/config.json'
        self.config_full = json.loads(open(self.config_path, 'r').read())

        self.timeframes = ['all', 'year', 'month']
        self.learning = [
                         'learnprogramming',
                         'learnpython',
                         'learngolang'
                        ]

        self.ai = ['neuralnetworks', 'statistics']

        self.language = [
                            'python',
                            'sql',
                            'julia',
                            'rlanguage',
                            'golang',
                            'cpp'
                        ]

        self.cstopics = [
                            'programming',
                            'proceduralgeneration',
                            'demoscene'
                        ]

        self.industry = [
                            'devops',
                            'webdev',
                            'coding',
                            'datasets'
                        ]

        self.entertainment = [
                                'softwaregore',
                                'programmerhumor',
                                'ImaginaryFeels',
                                'awww',
                                'ultrahdwallpapers',
                                'wallpapers',
                                'minimalwallpaper',
                                'DnDGreentext',
                                'shitdwarffortresssays'
                            ]

        self.categories = [
            self.learning,
            self.language,
            self.cstopics,
            self.ai,
            self.industry,
            self.entertainment
        ]

        # Makes a single composite of all the subreddits
        self.sub_reddit_composite = [subreddit for subreddit in chain(*self.categories)]

    async def reddit_bot(self):
        reddit_config = None #(Pseudocode: Read reddit_config from full_config)
        reddit = praw.Reddit(
            client_id=reddit_config['client_id'],
            client_secret=reddit_config['client_secret'],
            user_agent=reddit_config['user_agent'],
            username=reddit_config['username'],
            password=reddit_config['password']
        )
        self.reddit_bot.reddit = reddit
        return reddit

    async def topinxperiod(self, subreddit, period='year', return_quantity=3):
        try:
            if return_quantity > 7:
                return_quantity = 7

            # relevant documentation https://praw.readthedocs.io/en/latest/code_overview/models/subreddit.html
            content = [submission.url for submission in self.reddit.subreddit(
                subreddit).top(period, limit=return_quantity)]
            return content
        except Exception as e:
            print(str(e))

    async def readings_fetch(self, ctx, subreddits_list, period='year', mode='top'):
        top_links_in_period = []

        if mode == 'assorted':
            links_per_sub = 3
        else:
            links_per_sub = 5

        try:
            for subreddit in subreddits_list:
                top_links_in_period.extend(await self.topinxperiod(
                                                                    subreddit,
                                                                    period=period,
                                                                    return_quantity=links_per_sub
                                                                    )
                                        )
        except Exception as e:
            print(e)

        top_links_in_period = sample(top_links_in_period, 5)

        while len('\n'.join([str(x) for x in top_links_in_period])) > 2000:
            top_links_in_period.pop(-1)

        return '\n'.join([str(x) for x in top_links_in_period])

    @tasks.loop(seconds=86400)
    async def get_reddit(self, ctx, mode='assorted'):

        try:
            period = sample(self.timeframes, 1)[0]

            # category is a list of randomly sampled subreddit names to be concatenated after r/
            category = sample(self.sub_reddit_composite, 5)
            await ctx.send(await self.readings_fetch(ctx, category, period=period, mode=mode))

        except Exception as e:
            print(e)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def reddit(self, ctx, state: bool):
        """Enable or disable the reddit system"""
        config = self.config_full[str(ctx.message.guild.id)]
        if all((state is True, config["reddit_channel"] is None)):
            permission_overrides = {
                ctx.guild.default_role: PermissionOverwrite(send_messages=False),
                ctx.guild.me: PermissionOverwrite(send_messages=True)
            }
            channel = await ctx.message.guild.create_text_channel("reddit-feed", overwrites=permission_overrides)
            config.update(reddit_channel=channel.id)
            json.dump(self.config_full, open(self.config_path,
                                             'w'), indent=2, separators=(',', ': '))
        elif all((state is False, config["reddit_channel"] is not None)):
            channel = self.bot.get_channel(config["reddit_channel"])
            await channel.delete()
            config.update(reddit_channel=None)
            json.dump(self.config_full,
                      open(self.config_path, 'w'),
                      indent=2,
                      separators=(',', ': ')
                      )


def setup(bot):
    bot.add_cog(Reddit(bot))
