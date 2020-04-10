from discord.ext import commands, tasks
from discord import PermissionOverwrite, client
from random import sample

import json
import praw


def load_reddit_conf():
    config = json.loads(open('assets/config.json', 'r').read())
    return config["reddit_config"]

def __init__(self,bot):
    self.bot = bot
    self.reddit_config = self.bot.reddit_config

def reddit_bot():
    try:
        reddit = reddit_bot.reddit
        return reddit
    except Exception as e:
        reddit_config = load_reddit_conf()[0]
        reddit = praw.Reddit(
            client_id=reddit_config['client_id'],
            client_secret=reddit_config['client_secret'],
            user_agent=reddit_config['user_agent'],
            username=reddit_config['username'],
            password=reddit_config['password']
        )
        reddit_bot.reddit = reddit
        return reddit

async def topinxperiod(subreddit, period='year', return_quantity=3):
    try:
        if return_quantity > 7:
            return_quantity = 7

        reddit = reddit_bot()
        # relevant documentation https://praw.readthedocs.io/en/latest/code_overview/models/subreddit.html
        content = [submission.url for submission in reddit.subreddit(subreddit).top(period,limit=return_quantity)]
        return content
    except Exception as e:
        print(str(e))


async def readings_fetch(ctx, subreddits_list, period='year', mode='top'):
    top_links_in_period = []

    if mode == 'assorted':
        links_per_sub = 3
    else:
        links_per_sub = 5

    try:
        for subreddit in subreddits_list:
            top_links_in_period.extend(await topinxperiod(subreddit, period=period, return_quantity=links_per_sub))
    except Exception as e:
        print(e)

    top_links_in_period = sample(top_links_in_period, 5)

    while len('\n'.join([str(x) for x in top_links_in_period])) > 2000:
        top_links_in_period.pop(-1)

    return '\n'.join([str(x) for x in top_links_in_period])


async def test_top_readings(list_of_lists):
    periods = ['week', 'month', 'year']

    for period in periods:
        top_links_in_period = []
        for subreddit in list_of_lists[0]:
            top_links_in_period.extend(topinxperiod(subreddit, period))
        print(len(''.join(top_links_in_period)))

class Reddit(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    @tasks.loop(seconds=86400)
    async def get_reddit(self, ctx, mode='assorted'):

        try:
            Reddit.init
        except Exception as e:
            Reddit.init = True
            Reddit.timeframes = ['all', 'year', 'month']
            Reddit.learning = ['learnprogramming',
                                   'learnpython',
                                   'learngolang']

            Reddit.ai = ['neuralnetworks','statistics']

            Reddit.language = [
                                'python',
                                'sql',
                                'julia',
                                'rlanguage',
                                'golang',
                                'cpp'
                                ]

            Reddit.cstopics = [
                                'programming',
                                'proceduralgeneration',
                                'demoscene'
                            ]

            Reddit.industry = ['devops',
                                'webdev',
                                'coding',
                                'datasets'
                                ]

            Reddit.entertainment = ['softwaregore',
                                        'programmerhumor',
                                        'ImaginaryFeels',
                                        'awww',
                                        'ultrahdwallpapers',
                                        'wallpapers',
                                        'minimalwallpaper',
                                        'DnDGreentext',
                                        'shitdwarffortresssays'
                                        ]

            Reddit.categories = [
                Reddit.learning,
                Reddit.language,
                Reddit.cstopics,
                Reddit.ai,
                Reddit.industry,
                Reddit.entertainment
            ]

            # initilization for horrible abuse of the python language
            Reddit.sub_reddit_composite = []

            # horrible abuse of the python language. One line and it works. but feel free to make the below abuse/pythonic more readable.
            [Reddit.sub_reddit_composite.extend(x) for x in Reddit.categories]
        try:
            period = sample(Reddit.timeframes, 1)[0]

            # category is a list of subreddit names to be concatenated after r/
            category = sample(Reddit.sub_reddit_composite, 5)
            reddit_config = json.loads(open('assets/config.json', 'r').read())['reddit_channel']
            reddit_feed = client.get_channel(reddit_config)


            await reddit_feed.send(await readings_fetch(ctx,category, period=period, mode=mode))

        except Exception as e:
            print(e)

	@commands.command()
	@commands.has_permissions(manage_guild=True)
	async def reddit(self, ctx, state: bool):
		"""Enable or disable the reddit system"""
		config = self.config_full[str(ctx.message.guild.id)]
		if state is True and config["reddit"] is None:
            permission_overrides = {
                ctx.guild.default_role: PermissionOverwrite(send_messages=False)
                ctx.guild.me: PermissionOverwrite(send_messages=True)
            }
			channel = await ctx.message.guild.create_channel("reddit-feed", overwrites=permission_overrides)
			config.update(reddit_channel = channel.id)
			json.dump(self.config_full, open('assets/config.json', 'w'), indent=2, separators=(',', ': '))
		elif state is False and config["reddit_channel"] is not None:
			channel = bot.get_channel(config["reddit_channel"])
			await channel.delete()
			config.update(reddit_channel=None)
			json.dump(self.config_full, open('assets/config.json', 'w'), indent=2, separators=(',', ': '))

def setup(bot):
    bot.add_cog(Reddit(bot))

