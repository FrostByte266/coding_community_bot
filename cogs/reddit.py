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


async def topinxperiod(subreddit,period='year',return_quantity=3):
	if return_quantity > 7:
		return_quantity = 7

	response = requests.get(f'https://www.reddit.com/r/{subreddit}/top/?t={period}', headers=headers)


	soup = BeautifulSoup(response.text, features="html.parser")

	# SQnoC3ObvgnGjWt90zD9Z is the div class on reddit that containts the center panes list
	anchors = soup.find_all(class_="SQnoC3ObvgnGjWt90zD9Z")
	links = ['reddit.com' + x[x.find('href="') + 6:x.find('"><div')] for x in [str(x) for x in anchors]]

	return links[:return_quantity-1]


async def readings_fetch(subreddits_list,period='year',mode='top'):
	top_links_in_period = []

	if mode == 'assorted':
		links_per_sub = 5
	else:
		links_per_sub = 3

	for subreddit in subreddits_list:
		top_links_in_period.extend(topinxperiod(subreddit, period,links_per_sub))

		shuffle(top_links_in_period)
	while len('\n'.join([str(x) for x in top_links_in_period]))>2000:
		top_links_in_period.pop(-1)

	return '\n'.join([str(x) for x in top_links_in_period])

async def test_top_readings(list_of_lists):
	periods = ['day', 'week', 'month', 'year']

	for period in periods:
		top_links_in_period = []
		for subreddit in list_of_lists[0]:
			top_links_in_period.extend(topinxperiod(subreddit, period))
		print(len(''.join(top_links_in_period)))


class Reddit(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def get_reddit(self,ctx,mode='assorted'):
		try:
			await ctx.send(await readings_fetch(self.get_reddit.categories[2], 'year', mode))
		except Exception as E:
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
									   'java']

			self.get_reddit.cstopics = ['programming',
									   'compsci',
									   'proceduralgeneration',
									   'crypto',
									   'demoscene']

			self.get_reddit.categories = [self.get_reddit.learning,self.get_reddit.language,self.get_reddit.cstopics,get_reddit.ai]
			period = sample(['year','month','week','day'])
			await ctx.send(await readings_fetch(self.get_reddit.categories[2],period,mode))

def setup(bot):
    bot.add_cog(Reddit(bot))