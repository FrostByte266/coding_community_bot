from bs4 import BeautifulSoup
from discord.ext import commands
from random import sample, shuffle

import requests

headers = {
    'User-Agent': '',
    'Accept': '',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': '',
    'Connection': '',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}


def topinxperiod(subreddit, period='year', return_quantity=3):
    if return_quantity > 7:
        return_quantity = 7

    response = requests.get(f'https://www.reddit.com/r/{subreddit}/top/?t={period}', headers=headers)
    soup = BeautifulSoup(response.text, features="html.parser")

    # SQnoC3ObvgnGjWt90zD9Z is the div class on reddit that containts the center panes list
    anchors = soup.find_all(class_="SQnoC3ObvgnGjWt90zD9Z")
    links = ['https://www.reddit.com' + x[x.find('href="') + 6:x.find('"><div')] for x in [str(x) for x in anchors]]

    return links[:return_quantity - 1]


async def readings_fetch(ctx,subreddits_list, period='year', mode='top'):
    top_links_in_period = []

    if mode == 'assorted':
        links_per_sub = 3
    else:
        links_per_sub = 5

    await ctx.send('composite: ' + str(len(subreddits_list)))
    subreddits_list = sample(subreddits_list,5)


    for subreddit in subreddits_list:
        top_links_in_period.extend(topinxperiod(subreddit, period, links_per_sub))

    shuffle(top_links_in_period)
    top_links_in_period = sample(top_links_in_period,5)
    await ctx.send('composite: ' + str(len(top_links_in_period)))

    while len('\n'.join([str(x) for x in top_links_in_period])) > 2000:
        top_links_in_period.pop(-1)

    return '\n'.join([str(x) for x in top_links_in_period])


def test_top_readings(list_of_lists):
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
            period = sample(self.get_reddit.timeframes, 1)
            category = sample(self.get_reddit.sub_reddit_composite, 5)
            await ctx.send(readings_fetch(category, period, mode))
        except Exception as E:
            self.get_reddit.timeframes = ['year', 'month']
            self.get_reddit.learning = ['learnprogramming',
                                        'learnpython',
                                        'learnlisp',
                                        'learngolang',
                                        'learnjava',
                                        'cscareerquestions']

            self.get_reddit.ai = ['neuralnetworks',
                                  'deeplearning',
                                  'machinelearning',
                                  'statistics']

            self.get_reddit.language = ['python',
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

            self.get_reddit.cstopics = ['programming',
                                        'compsci',
                                        'proceduralgeneration',
                                        'crypto',
                                        'demoscene'
                                        ]

            self.get_reddit.industry = ['devops',
                                        'TechnicalDebt',
                                        'webdev',
                                        'coding',
                                        'datasets']

            self.get_reddit.entertainment = ['softwaregore',
                                             'ProgrammerHumor',
                                             'ImaginaryFeels',
                                             'Awww',
                                             'ultrahdwallpapers',
                                             'wallpapers',
                                             'MinimalWallpaper',
                                             'DnDGreentext',
                                             'ShitDwarfFortressSays'
                                             ]

            self.get_reddit.categories = [
                                            self.get_reddit.learning,
                                            self.get_reddit.language,
                                            self.get_reddit.cstopics,
                                            self.get_reddit.ai,
                                            self.get_reddit.industry,
                                            self.get_reddit.entertainment
                                        ]

            #initilization for horrible abuse of the python language
            self.get_reddit.sub_reddit_composite = []

            #horrible abuse of the python language. One line and it works. but feel free to make the below abuse/pythonic more readable.
            [self.get_reddit.sub_reddit_composite.extend(x) for x in self.get_reddit.categories]


            #category is a list of subreddit names to be concatenated after r/
            category = sample(self.get_reddit.sub_reddit_composite,5)


            period = sample(self.get_reddit.timeframes, 1)
            await ctx.send( await readings_fetch(ctx,category, period, mode))

    @get_reddit.error
    async def get_reddit_error(self, ctx, error):
        await ctx.send(f'Encountered an error: {error}')


def setup(bot):
    bot.add_cog(Reddit(bot))
