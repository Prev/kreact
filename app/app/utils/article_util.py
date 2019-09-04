from model.timedivision import TimeDivision
from adapter.articles import fill_more_info


def list2timediv(articles):
	""" Convert List<Article> to TimeDivision<Article>
	:return:
	"""
	td = TimeDivision(default_value=[])
	for article in articles:
		td.append_list(article.date, article)
	return td


def divided_posneg(articles, keywords):
	""" Get data divided by timelabel with extracted sentiments.
	:param articles: List<model.Article>
	:param keywords: List<String>
	"""
	article_div = list2timediv(articles)  # TimeDivision of List<model.Article>

	return [
		(
			sum([a.sympathy(keywords) for a in articles]),
			sum([a.antipathy(keywords) for a in articles]),
		) for articles in article_div.values()
	]


def hottest_articles_info(articles, keywords, n=6):
	""" Get hottest articles and there info (including title and URL)
	:param articles: List<model.Article>
	:return: List<model.Article>
	:param keywords: List<String>
	:param n: number of hottest articles
	"""
	new_list = [(a, a.sympathy(keywords) + a.antipathy(keywords)) for a in articles]
	new_list = sorted(new_list, key=lambda x: x[1], reverse=True)

	articles = [t[0] for t in new_list[0:n]]

	fill_more_info(articles)

	return articles


def neighbors(articles, keywords):
	""" Get neighbors of args(means list of topics)
	Fetch common article from Redis, and count the number of times that other token has apeared
	:param articles: List<model.Article>
	:param keywords: List<String>
	:return: List of (neighbor, Group-by-date weights) descending order by weight
	"""
	ret = {}
	for article in articles:
		for keyword in article.keywords():
			# Iterate all keywords of each articles

			if keyword in keywords:
				# If current keyword is one of keywords, ignore
				continue

			if keyword not in ret:
				# Init new TimeDivision in this keyword
				ret[keyword] = TimeDivision(default_value=0)

			# Increase target date's value by weight
			ret[keyword].increase(
				datetime=article.date,
				value=article.weight_keywords(keywords + [keyword])
			)

	# Normalize with base weight
	# Base = tf-idf(p) / tf-idf(max of doc)^2
	base = sum([
		article.weight_keywords(list(keywords)) / article.max_keyword_weight
		for article in articles
	])

	for timelabel in TimeDivision.all_labels():
		for neighbor, weight_div in ret.items():
			# Set value to normalized
			weight_div.set(
				datetime=timelabel,
				value=weight_div.get(timelabel) / max(base, 1)
			)

	return ret.items()
