from discord.ext import commands
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

    @commands.command()
    async def get_reddit(self, ctx, mode='assorted'):

        try:
            Reddit.init
        except Exception as e:
            Reddit.init = True
            Reddit.timeframes = ['all', 'year', 'month']
            Reddit.learning = ['learnprogramming',
                                   'learnpython',
                                   'learnlisp',
                                   'learngolang',
                                   'learnjava',
                                   'cscareerquestions']

            Reddit.ai = ['neuralnetworks',
                             'deeplearning',
                             'machinelearning',
                             'statistics']

            Reddit.language = ['python',
                                   'sql',
                                   'julia',
                                   'lisp',
                                   'rlanguage',
                                   'golang',
                                   'rust',
                                   'java',
                                   'javascript',
                                   'haskell',
                                   'cpp',
                                   'scala']

            Reddit.cstopics = ['programming',
                                   'compsci',
                                   'proceduralgeneration',
                                   'crypto',
                                   'demoscene'
                                   ]

            Reddit.industry = ['devops',
                                   'technicaldebt',
                                   'webdev',
                                   'coding',
                                   'datasets']

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
            await ctx.send(await readings_fetch(ctx,category, period=period, mode=mode))

        except Exception as e:
            print(e)

def setup(bot):
    bot.add_cog(Reddit(bot))

