from abc import *


class Article:

	def __init__(self, id, title, content, date, url):
		self.id = id
		self.title = title
		self.content = content
		self.date = date
		self.url = url

	@abstractmethod
	def sympathy(self):
		pass

	@abstractmethod
	def antipathy(self):
		pass


class PreprocessedArticle(Article):

	def __init__(self, id, date, sympathy, antipathy, relation_entries):
		""" In realtime API server, we don't need full article information,
			just for count of comments, and 'pos/neg' information.

			This class inherits `Article` class, which is general model for article,
			but contains minimum data to operate service.

			So `title`, `content`, and `url` are not used in this class,
			only `comments_cnt`, `sympathy`, and `antipathy` exist.
		"""
		Article.__init__(self, id, None, None, date, None)
		self._sympathy = sympathy
		self._antipathy = antipathy

		# build_relation_map
		frequent_nouns = []

		if relation_entries:
			for tf_entries in relation_entries:
				x = tf_entries.split(':')
				frequent_nouns.append((x[1], float(x[0])))

			self.max_keyword_weight = frequent_nouns[0][1]
		self._keyword2weight = dict(frequent_nouns)

	def sympathy(self, keywords=None):
		""" Get sympathy (positive reactions)
		:param keywords: If not None, multiply weight of keywords in this article
		:return: Float
		"""
		if keywords is None:
			return self._sympathy
		else:
			return float(self._sympathy) * self.weight_keywords(keywords)

	def antipathy(self, keywords=None):
		""" Get antipathy (negative reactions)
		:param keywords: If not None, multiply weight of keywords in this article
		:return: Float
		"""
		if keywords is None:
			return self._antipathy
		else:
			return float(self._antipathy) * self.weight_keywords(keywords)

	def keywords(self):
		""" Get keywords in this article
		:return: List of String
		"""
		return self._keyword2weight.keys()

	def weight_keywords(self, keywords):
		""" Get weight of keywords in this article
		:param keywords: List of keywords
		:return: Float
		"""
		ret = 1.0
		for keyword in keywords:
			ret *= self._keyword2weight[keyword] / self.max_keyword_weight
		return ret

	@staticmethod
	def fromredis(id, row):
		""" In redis, pre-processed article information is saved with key 'a-info:{id}'.
			This functions is to parse that data and returns `PreprocessedArticle` class.
		"""
		entries = row.split('/')
		date, pos, neg = entries[0:3]
		relation_entries = entries[3:]

		if len(relation_entries) == 1 and relation_entries[0] == '':
			relation_entries = None

		a = PreprocessedArticle(
			id=id,
			date=date,
			sympathy=int(pos),
			antipathy=int(neg),
			relation_entries=relation_entries,
		)
		return a
