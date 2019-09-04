from driver.redis import conn as redis_conn
from model.article import PreprocessedArticle


def get_articles(keywords):
	""" Get common articles between arguments
	:param keywords: List of keywords
	:return: List<model.Article>
	"""
	r = redis_conn()

	keys = ['t2a:%s' % keyword for keyword in keywords]
	ids = [x.decode('utf-8') for x in r.sinter(*keys)]

	if len(ids) == 0:
		return []

	# Use redis pipeline to speed up performance
	pipe = r.pipeline()
	for aid in ids:
		pipe.get('a-info:%s' % aid)
	rows = pipe.execute()

	ret = []
	for index, row in enumerate(rows):
		a = PreprocessedArticle.fromredis(
			id=ids[index],
			row=row.decode()
		)
		ret.append(a)
	return ret


def recent_articles():
	""" Get recent articles in redis
	:return: List<model.Article>
	"""
	r = redis_conn()
	last_id = int(r.get('last-id').decode())

	ids = range(last_id-5000, last_id)

	pipe = r.pipeline()
	for aid in ids:
		pipe.get('a-info:%s' % aid)
	rows = pipe.execute()

	ret = []
	for row in rows:
		if row is None:
			continue

		ret.append(PreprocessedArticle.fromredis(
			id=0,
			row=row.decode()
		))

	return ret


def fill_more_info(articles):
	""" Fill more information to given articles
	:param articles: List<model.Article>
	"""
	r = redis_conn()

	ids = [article.id for article in articles]

	pipe = r.pipeline()
	for aid in ids:
		pipe.get('a-info2:%s' % aid)
	rows = pipe.execute()

	for index, row in enumerate(rows):
		data = row.decode()
		title, url = data.split('\n')
		articles[index].title = title
		articles[index].url = url
