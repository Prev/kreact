"""
All data is provided to divided group by time (Like per-month or per-week)
to see change of data (total weight, positive, or negative).
To satisfy this demand, We use custom data structure, called `TimeDivision`.
"""
from datetime import date, timedelta
from flask import request

class TimeDivision:

	@staticmethod
	def get_timeunit():
		return request.args.get('timeunit', 'month')

	# TIMELABEL_UNIT = 'month'
	_all_labels_cache = {}

	@staticmethod
	def all_labels():
		cache_id = '%s/%s' % (date.today(), TimeDivision.get_timeunit())
		if cache_id in TimeDivision._all_labels_cache:
			return TimeDivision._all_labels_cache[cache_id]

		d = timedelta(days=1)
		cur = date(2017, 6, 1) # Base
		end = date(2018, 10, 17) #date.today()

		ret = [TimeDivision.timelabel(cur)]

		while True:
			if (end - cur).total_seconds() == 0:
				# Loop until today
				break

			cur += d
			label = TimeDivision.timelabel(cur)
			if ret[-1] != label:
				ret.append(label)

		ret = ret[-12:]
		TimeDivision._all_labels_cache[cache_id] = ret
		return ret

	@staticmethod
	def timelabel(datetime):
		""" Convert datetime string to timelabel
			Default conversion is YY.mm. (ex. 18.06.)
		:param datetime: String or Date instance
		:return: String
		"""
		if type(datetime) == str and len(datetime) > 10 and datetime[4] == '-' and datetime[7] == '-':
			# Parse str to date if it has correct format
			datetime = date(int(datetime[0:4]), int(datetime[5:7]), int(datetime[8:10]))

		if type(datetime) == date:
			if TimeDivision.get_timeunit() == 'month':
				return datetime.strftime('%y.%m.')

			elif TimeDivision.get_timeunit() == 'week':
				saturday = datetime + timedelta(days=6-datetime.isoweekday()%7)
				# day under 7 -> week1, day under 14 -> week n, ...
				week = (saturday.day-1) / 7 + 1
				return saturday.strftime('%y.%m.') + (' %d\'' % week)

			else:
				raise Exception('Unsupported TIMELABEL_UNIT')

		# Use raw str if no format matched
		return datetime

	def __init__(self, default_value=None):
		self._data = {}
		self._default_value = default_value

	def get(self, datetime):
		""" Get value in specific timelabel division
		:param datetime: String
		:return: Value set by `set`, `append`, or `increase` method
		"""
		return self._data.get(TimeDivision.timelabel(datetime), self._default_value)

	def set(self, datetime, value):
		""" Set value of division in specific timelabel division
		:param datetime: String
		:param value: Anything
		"""
		self._data[TimeDivision.timelabel(datetime)] = value

	def append_list(self, datetime, value):
		""" Append value like list to specific timelabel division
		:param datetime: String
		:param value: Item to be append
		"""
		timelabel = TimeDivision.timelabel(datetime)

		if timelabel not in self._data:
			self._data[timelabel] = []

		self._data[timelabel].append(value)

	def increase(self, datetime, value=1):
		""" Increase to specific timelabel division
		If the division is not set, init to 0 first
		:param datetime: String
		:param value: Value to increase
		"""
		timelabel = TimeDivision.timelabel(datetime)
		if timelabel not in self._data:
			self._data[timelabel] = 0
		self._data[timelabel] += value

	def items(self):
		""" Get list of <timelabel, value> sorted by timelabel
		:return: List<Tuple<timelabel, value>>
		"""
		return [
			(timelabel, self.get(timelabel))
			for timelabel in TimeDivision.all_labels()
		]

	def values(self):
		""" Get list of value sorted by timelabel
		:return: List<timelabel, value>
		"""
		return [self.get(timelabel) for timelabel in TimeDivision.all_labels()]
