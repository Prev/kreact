import redis
import settings

_db_instance = None


def conn():
	""" Get Redis connection singleton object
	"""
	global _db_instance

	if _db_instance:
		return _db_instance
	else:
		_db_instance = redis.Redis(
			host=settings.REDIS_HOST,
			password=settings.REDIS_PASS,
			db=settings.REDIS_DB,
		)
		return _db_instance
