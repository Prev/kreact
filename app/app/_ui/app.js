'use strict';

var app = angular.module('uiApp', ['ngRoute', 'angular-loading-bar']);

var POS_COLOR = "#448AFF";
var NEG_COLOR = "#D50000";

function location2keyword(location) {
	var keywords = location;
	if (keywords[0]) keywords = keywords.substr(1);
	return keywords.split('/').join('+');
}

function keyword2location(keyword) {
	return keyword.split('+').join('/');
}

function joinPosNegAndTimelabel(posnegArr, timelabelArr) {
	var ret = [];
	for (var i = 0; i < timelabelArr.length; i++) {
		ret.push({
			'timelabel': timelabelArr[i],
			'pos': posnegArr[i][0],
			'neg': posnegArr[i][1]
		})
	}
	return ret;
}

function preprocessRelatedTopics(relatedTopics, periodType) {
	var ret = [];

	for (var topicItem of relatedTopics) {
		var posneg = topicItem.posneg;
		var co_occurrence = topicItem.co_occurrence;

		switch (periodType) {
			case 'allperiods':
				// Use all data
				break;

			case 'recent6':
				// Use recent 6 data
				posneg = posneg.slice(-7, -1);
				co_occurrence = co_occurrence.slice(-7, -1);
				break;

			case 'recent1':
				// Use recent 1 data
				posneg = posneg.slice(-1);
				co_occurrence = co_occurrence.slice(-1);
				break;

			default:
				throw Error('Unsupported period "'+periodType+'"');
		}

		ret.push({
			topic: topicItem.topic,
			pos: _.sumBy(posneg, function (o) { return o[0] }), // sum
			neg: _.sumBy(posneg, function (o) { return o[1] }), // sum
			co_occurrence: _.sum(co_occurrence) / co_occurrence.length // average
		});
	}

	return _.sortBy(ret, function (o) { return o.co_occurrence }).reverse().slice(0, 6);
}

app.config(function(cfpLoadingBarProvider) {
	cfpLoadingBarProvider.includeSpinner = false;
});

app.run(function($rootScope) {
	$rootScope.location2keyword = location2keyword;
	$rootScope.keyword2location = keyword2location;

	$rootScope.today = {
		// month: (new Date()).getMonth() + 1,
		// date: (new Date()).getDate(),
		month: 10,
		date: 17,
	};
});


app.controller('MainController', function ($scope, $location, $http, $q) {
	$scope.searchingKeyword = location2keyword($location.path());

	$scope.search = function() {
		$location.path('/' + $scope.searchingKeyword.split('+').join('/'));
	};

	$scope.$on('$locationChangeSuccess', function() {
		var api = $location.path();
		$scope.keyword = location2keyword($location.path());

		if (!$scope.keyword) return;

		$scope.searchingKeyword = $scope.keyword;

		$scope.weeklyPosNeg = [];
		$scope.monthlyPosNeg = [];
		$scope.relatedTopicsA = null;
		$scope.relatedTopicsR6 = null;
		$scope.relatedTopicsR1 = null;
		$scope.mainNews = [];

		$q.all([
			$http({url: api, method: 'GET'}),
			$http({url: api + '?timeunit=week', method: 'GET'})

		]).then(function (responses) {
			// Monthly data
			var monthly = responses[0].data;
			var timelabels = monthly.timelabel;

			// Pre-process data for monthly pos-neg trends and related topics
			$scope.monthlyPosNeg = joinPosNegAndTimelabel(monthly.posneg, timelabels).reverse();

			$scope.relatedTopicsA = preprocessRelatedTopics(monthly.related_topics, 'allperiods');
			$scope.relatedTopicsR6 = preprocessRelatedTopics(monthly.related_topics, 'recent6');
			$scope.relatedTopicsR1 = preprocessRelatedTopics(monthly.related_topics, 'recent1');

			$scope.mainNews = monthly.main_news;

			// Weekly data
			var weekly = responses[1].data;
			var timelabels2 = weekly.timelabel.map(function (o) { return o.substr(3) });

			$scope.weeklyPosNeg = joinPosNegAndTimelabel(weekly.posneg, timelabels2).reverse();
		});
	});

	if (!$scope.keyword) {
		$http({url: '/_hot?n=6', method: 'GET'})
			.then(function (response) {
				$scope.hotTopics = response.data;
			});
	}
});


app.directive('posnegChart', function() {
	/**
	 * Render Chart.js by response of API
	 */
	function renderChart(dom, data) {
		dom.html('');

		if (data.length === 0)
			return;

		function barItems(d) {
			return [
				{ x: d.timelabel, value: d.pos },
				{ x: d.timelabel, value: d.neg },
			];
		}

		var d3Data = data.map(function (d) {
			return {
				'timelabel': d.timelabel,
				'pos': d.pos,
				'neg': -d.neg,
			};
		}).reverse();

		var svg = d3.select(dom[0]),
			margin = {top: 20, right: 20, bottom: 30, left: 40},
			width = +svg.attr("width") - margin.left - margin.right,
			height = +svg.attr("height") - margin.top - margin.bottom,
			g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

		var x = d3.scaleBand()
			.rangeRound([0, width])
			.paddingInner(0.4)
			.align(0.1);

		var y = d3.scaleLinear()
			.rangeRound([height, 0]);

		x.domain(d3Data.map(function(d) { return d.timelabel; }));
		y.domain([
			d3.min(d3Data, function(d) { return d.neg; }),
			d3.max(d3Data, function(d) { return d.pos; })
		]).nice();

		g.append("g")
			.selectAll("g")
			.data(d3Data)
			.enter().append("g")
				.attr("class", "bar")
			.selectAll("rect")
			.data(function (d) { return barItems(d); })
			.enter().append("rect")
			  	.attr("x", function(d) { return x(d.x); })
			  	.attr("y", function(d) { return y(Math.max(0, d.value)) + 0.5; })
			  	.attr("height", function(d) { return Math.max(Math.abs(y(d.value) - y(0)) - 1, 0); })
				.attr("width", x.bandwidth())
				.style("fill", function(d) { return d.value > 0 ? POS_COLOR : NEG_COLOR });

		g.append("g")
		  	.attr("class", "axis")
		  	.attr("transform", "translate(0," + height + ")")
		  	.call(d3.axisBottom(x));

		g.append("g")
		  	.attr("class", "axis")
		  	.call(d3.axisLeft(y).ticks(null, "s"));

		g.append("g")
			.attr("class", "center axis")
		.append("line")
			.attr("y1", y(0))
			.attr("y2", y(0))
			.attr("x2", width);
	}

	return {
		restrict: 'E',
		scope: {
			data: '='
		},
		template: '<svg width="500" height="250"></svg>',
		link: function(scope, element, attrs) {
			var dom = element.find('svg');

			if (!scope.data) {
				scope.$watch('data', function() {
					if (scope.data)
						renderChart(dom, scope.data);
				});

			}else{
				renderChart(dom, scope.data);
			}
		}
	};
});



app.directive('donutChart', function() {
	var width = 96,
		height = 96,
		radius = Math.min(width, height) / 2;

	var color = d3.scaleOrdinal()
		.range([NEG_COLOR, POS_COLOR]);

	var arc = d3.arc()
		.outerRadius(radius)
		.innerRadius(radius - 10);

	var pie = d3.pie()
		.sort(null)
		.value(function(d) { return d.value; });

	function renderChart(dom, topicItem) {
		dom.html('');

		// var dataSliced = effectiveData(topicItem.data, period);
		var d3Data = [
			{'label': '부정', 'value': topicItem.neg},
			{'label': '긍정', 'value': topicItem.pos},
		];

		var svg = d3.select(dom[0])
			.attr("width", width)
			.attr("height", height)
		.append("g")
			.attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

		var g = svg.selectAll(".arc")
			.data(pie(d3Data))
		.enter().append("g")
			.attr("class", "arc");

		g.append("path")
			.attr("d", arc)
			.style("fill", function(d) { return color(d.data.label); });

		if (topicItem.co_occurrence) {
			g.append("text")
				.attr("dy", "-.15em")
				.style("text-anchor", "middle")
				.attr("class", "label")
				.text(topicItem.topic);

			g.append("text")
				.attr("dy", "1em")
				.style("text-anchor", "middle")
				.attr("class", "label sub")
				.text(_.round(topicItem.co_occurrence * 100, 2) + '%');
		}else {
			g.append("text")
				.attr("dy", ".35em")
				.style("text-anchor", "middle")
				.attr("class", "label")
				.text(topicItem.topic);
		}
	}

	return {
		restrict: 'E',
		scope: {
			data: '='
		},
		template: '<svg></svg>',
		link: function(scope, element, attrs) {
			var dom = element.find('svg');

			if (!scope.data) {
				scope.$watch('data', function() {
					if (scope.data)
						renderChart(dom, scope.data);
				});

			}else{
				renderChart(dom, scope.data);
			}
		}
	};
});
