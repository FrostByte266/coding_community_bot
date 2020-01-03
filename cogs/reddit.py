from discord.ext import commands
from random import sample

import praw

def __init__(self,bot):
    self.bot = bot
    self.reddit_config = self.bot.reddit_config

async def reddit_bot():
    bot = commands.Bot()

    bot.reddit_stuffzz = bot.config_full['reddit things']
    try:
        bot.reddit_init
    except Exception as e:
        bot.init = True
        bot.reddit = praw.Reddit(
            client_id=bot.reddit_config['client_id'],
            client_secret=bot.reddit_config['client_secret'],
            user_agent=bot.reddit_config['user_agent'],
            username=bot.reddit_config['username'],
            password=bot.reddit_config['password']
        )

async def topinxperiod(subreddit, period='year', return_quantity=3):

    try:
        if return_quantity > 7:
            return_quantity = 7

        reddit = reddit_bot.reddit
        #print(reddit.read_only)
        # relevant documentation https://praw.readthedocs.io/en/latest/code_overview/models/subreddit.html
        return [submission.url for submission in reddit.subreddit(subreddit).top(period,limit=return_quantity)]
    except Exception as e:
        return str(e)


async def readings_fetch(ctx, subreddits_list, period='year', mode='top'):
    top_links_in_period = []

    if mode == 'assorted':
        links_per_sub = 3
    else:
        links_per_sub = 5

    print(str(subreddits_list))
    try:
        for subreddit in subreddits_list:
            top_links_in_period.extend(topinxperiod(subreddit, period, links_per_sub))
    except Exception as e:
        print(e)

    print('\ntop links: ' + str(len(top_links_in_period)))
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
        Reddit.reddit = await reddit_bot.reddit

        try:
            Reddit.reddit.init
        except Exception as e:
            Reddit.reddit.init = True
            Reddit.reddit.timeframes = ['all', 'year', 'month']
            Reddit.reddit.learning = ['learnprogramming',
                                   'learnpython',
                                   'learnlisp',
                                   'learngolang',
                                   'learnjava',
                                   'cscareerquestions']

            Reddit.reddit.ai = ['neuralnetworks',
                             'deeplearning',
                             'machinelearning',
                             'statistics']

            Reddit.reddit.language = ['python',
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

            Reddit.reddit.cstopics = ['programming',
                                   'compsci',
                                   'proceduralgeneration',
                                   'crypto',
                                   'demoscene'
                                   ]

            Reddit.reddit.industry = ['devops',
                                   'technicaldebt',
                                   'webdev',
                                   'coding',
                                   'datasets']

            Reddit.reddit.entertainment = ['softwaregore',
                                        'programmerhumor',
                                        'ImaginaryFeels',
                                        'awww',
                                        'ultrahdwallpapers',
                                        'wallpapers',
                                        'minimalwallpaper',
                                        'DnDGreentext',
                                        'shitdwarffortresssays'
                                        ]

            Reddit.reddit.categories = [
                Reddit.reddit.learning,
                Reddit.reddit.language,
                Reddit.reddit.cstopics,
                Reddit.reddit.ai,
                Reddit.reddit.industry,
                Reddit.reddit.entertainment
            ]

            # initilization for horrible abuse of the python language
            Reddit.reddit.sub_reddit_composite = []

            # horrible abuse of the python language. One line and it works. but feel free to make the below abuse/pythonic more readable.
            [Reddit.reddit.sub_reddit_composite.extend(x) for x in Reddit.reddit.categories]
        try:
            period = sample(Reddit.reddit.timeframes, 1)[0]

            # category is a list of subreddit names to be concatenated after r/
            category = sample(Reddit.reddit.sub_reddit_composite, 5)
            print(readings_fetch(category, period, mode))

        except Exception as e:
            print(e)


def setup(bot):
    bot.add_cog(Reddit(bot))

