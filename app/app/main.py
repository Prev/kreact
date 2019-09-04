"""
Topic Trends API Server
Graduation project in Hanyang University

@author github.com/Prev
@author github.com/thjeong917
"""

from flask import Flask, jsonify, request

import settings
from model.timedivision import TimeDivision
from adapter.articles import recent_articles, get_articles
from utils import article_util

app = Flask(__name__, static_folder='_ui')


@app.route('/')
def index():
	return app.send_static_file('app.html')


@app.route('/favicon.ico')
def favicon():
	return app.send_static_file('favicon.ico')


@app.route('/_hot')
def _hot_topics():
	keywords_posneg = {}
	n = int(request.args.get('n', 10))

	if n not in range(1, 20):
		return jsonify({'error': 'n is allowed between 1 and 20'})

	for article in recent_articles():
		for keyword in article.keywords():
			if keyword not in keywords_posneg:
				keywords_posneg[keyword] = [0, 0]

			keywords_posneg[keyword][0] += article.sympathy([keyword])
			keywords_posneg[keyword][1] += article.antipathy([keyword])

	ret = sorted(keywords_posneg.items(), key=lambda x: x[1][0]+x[1][1], reverse=True)[0:n]
	return jsonify([{'topic': x[0], 'pos': x[1][0], 'neg': x[1][1]} for x in ret])


@app.route('/<path:keywords>')
def search(keywords):
	if request.args.get('timeunit', 'month') not in ('month', 'week'):
		return jsonify({'error': 'Unsupported timeunit'})

	keywords = keywords.split('/')
	if len(keywords) >= 2 and keywords[-1] == '':
		keywords = keywords[0:-1]

	articles = get_articles(keywords)
	posneg_data = article_util.divided_posneg(articles, keywords)
	main_news = [{
		'title': a.title,
		'url': a.url,
		'date': a.date,
		'pos': a.sympathy(keywords),
		'neg': a.antipathy(keywords),
	} for a in article_util.hottest_articles_info(articles, keywords)]


	##################################
	# Procedure for related_topics
	##################################
	relations = article_util.neighbors(articles, keywords)

	# Pick 6 neighbors by sum all values or sum recent 6 timelabels or sum recent 1 timelabel
	# Format: { keyword1: weight1, keyword2: weight2, ... }
	friends_allperiods = dict(sorted(relations, key=lambda x: sum(x[1].values()), reverse=True)[0:6])
	friends_recent6 = dict(sorted(relations, key=lambda x: sum(x[1].values()[-6:]), reverse=True)[0:6])
	friends_recent1 = dict(sorted(relations, key=lambda x: x[1].values()[-1], reverse=True)[0:6])

	# Candidates are including 3 types of friends
	candidates = set(friends_allperiods.keys()) | set(friends_recent6.keys()) | set(friends_recent1.keys())

	related_topics = []
	for neighbor, weight_div in relations:
		if neighbor not in candidates:
			continue

		keywords2 = keywords + [neighbor]
		articles2 = get_articles(keywords2)

		related_topics.append({
			'topic': neighbor,
			'posneg': article_util.divided_posneg(articles2, keywords2),
			'co_occurrence': weight_div.values(),
		})

	# Result dictionary
	return jsonify({
		'timelabel': TimeDivision.all_labels(),
		'posneg': posneg_data,
		'main_news': main_news,
		'related_topics': related_topics,
	})


if __name__ == '__main__':
	app.run(
		host=settings.FLASK_APP_HOST,
		port=settings.FLASK_APP_PORT,
		debug=settings.DEBUG,
	)
