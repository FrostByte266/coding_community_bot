from random import shuffle

from bs4 import BeautifulSoup
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


def topinxperiod(subreddit,period='year',return_quantity=3):
	if return_quantity > 7:
		return_quantity = 7
	if period =='year':
		response = requests.get('https://www.reddit.com/r/' + subreddit + '/top/?t=year', headers=headers)
	elif period == 'month':
		response = requests.get('https://www.reddit.com/r/' + subreddit + '/top/?t=month', headers=headers)
	elif period == 'week':
		response = requests.get('https://www.reddit.com/r/' + subreddit + '/top/?t=week', headers=headers)
	elif period == 'day':
		response = requests.get('https://www.reddit.com/r/' + subreddit + '/top/?t=day', headers=headers)
	else:
		response = requests.get('https://www.reddit.com/r/' + subreddit + '/top/?t=year', headers=headers)

	soup = BeautifulSoup(response.text, features="html.parser")

	# SQnoC3ObvgnGjWt90zD9Z is the div class on reddit that containts the center panes list
	anchors = soup.find_all(class_="SQnoC3ObvgnGjWt90zD9Z")
	links = ['reddit.com' + x[x.find('href="') + 6:x.rfind('/"><h2 ') - 1] for x in [str(x) for x in anchors]]

	return links[:return_quantity-1]


def readings_fetch(subreddits_list,period='year',mode='top'):
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

def test_top_readings(list_of_lists):
	periods = ['day', 'week', 'month', 'year']

	for period in periods:
		top_links_in_period = []
		for subreddit in list_of_lists[0]:
			top_links_in_period.extend(topinxperiod(subreddit, period))
		print(len(''.join(top_links_in_period)))


def get_reddit(mode='assorted'):
	subreddit_learning = ['learnprogramming',
								'learnpython',
								'learnlisp',
								'learngolang',
								'learnjava',
								'cscareerquestions']

	subreddit_ai = ['neuralnetworks',
						 'deeplearning',
						 'machinelearning',
						 'statistics']

	subreddit_language = ['python',
							   'sql',
							   'julia',
							   'lisp',
							   'rlanguage',
							   'golang',
							   'rust',
							   'java']

	subreddit_cstopics = ['programming',
							   'compsci',
							   'proceduralgeneration',
							   'crypto',
							   'demoscene']

	subreddit_categories = [subreddit_learning,subreddit_language,subreddit_cstopics,subreddit_ai]


	print(readings_fetch(subreddit_categories[2],'year',mode))