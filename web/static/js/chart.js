let gridChart;
let pieChart;
let topBotsChart;
let topSubsChart;

function refreshCharts(data, time) {
	data = data['data'];
	let graph = data['graph'];
	let goodVotes = data['goodStats']['votes']['count'];
	let badVotes = data['badStats']['votes']['count'];
	let topBots = data['bots'];
	let topSubs = data['subs'];
	let ctx = document.getElementById('votes').getContext('2d');
	let ctxPie = document.getElementById('votesPie').getContext('2d');
	let ctxTopBots = document.getElementById('topBots').getContext('2d');
	let ctxSubsBots = document.getElementById('topSubs').getContext('2d');
	let linePoint;
	if (time.indexOf('d') > -1) {
		linePoint = new Date().getHours();
	} else if (time.indexOf('w') > -1) {
		let d = new Date();
		let weekday = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
		linePoint = weekday[d.getDay()];
	} else if (time.indexOf('M') > -1) {
		linePoint = new Date().getDate();
	} else if (time.indexOf('y') > -1) {
		let d = new Date();
		let month = ['January', 'February', 'March', 'April', 'May', 'June',
  						'July', 'August', 'September', 'October', 'November', 'December'];
		linePoint = month[d.getMonth()];
	}
	gridChart = new Chart(ctx, {
		type: 'line',
		data: {
			'labels': graph['labels'],
			'datasets': [
				{
					'label': 'Bad Bot Votes',
					'data': graph['votes'].map(vote => { return vote['bad']}),
					'fill': true,
					'tension': 0.4,
					'backgroundColor': 'rgba(255, 0, 0, 1)'
				},
				{
					'label': 'Good Bot Votes',
					'data': graph['votes'].map(vote => { return vote['good']}),
					'fill': true,
					'tension': 0.4,
					'backgroundColor': 'rgba(0, 0, 255, 1)'
				},
				{
					'label': 'Total Votes',
					'data': graph['votes'].map(vote => { return vote['bad'] + vote['good']}),
					'fill': true,
					'tension': 0.4,
					'backgroundColor': 'rgba(128, 0, 128, 1)'
				}
			]
		},
		options: {
			maintainAspectRatio: false,
			scales: {
				x: {
					grid: {
						color: '#d9d9d9'
					},
					title: {
						display: true,
						text: 'Timeline'
					}
				},
				y: {
					grid: {
						color: '#d9d9d9'
					},
					title: {
						display: true,
						text: 'Number of Votes'
					}
				}
			},
			plugins: {
				annotation: {
					annotations: {
						now: {
							type: 'line',
							xMin: linePoint,
							xMax: linePoint,
							borderColor: 'red',
							label: {
								content: 'Now',
								enabled: true,
								position: 'start'
							}
						}
					}
				}
			}
		}
	});
	pieChart = new Chart(ctxPie, {
		type: 'doughnut',
		data: {
			'labels': ['Good Bot Votes', 'Bad Bot Votes'],
			'datasets': [
				{
					'data': [goodVotes, badVotes],
					'backgroundColor': ['rgba(0, 255, 0, 1)', 'rgba(255, 0, 0, 1)']
				}
			]
        },
		options: {
			maintainAspectRatio: false
		}
	});
	let polarOptions = {
			scales: {
				radial: {
					grid: {
						color: '#d9d9d9'
					}
				}
			},
			maintainAspectRatio: false
		};
	topBotsChart = new Chart(ctxTopBots, {
		type: 'polarArea',
		data: {
			'labels': topBots.map(bot => { return bot['name']}),
			'datasets': [
				{
					'data': topBots.map(bot => {return (bot['votes']['good'] + 1) / (bot['votes']['bad'] + 1)}),
					'backgroundColor': [
						'rgba(0, 255, 0, 1)',
						'rgba(255, 0, 0, 1)',
						'rgba(0, 0, 255, 1)',
						'rgba(255, 255, 0, 1)',
						'rgba(255, 0, 255, 1)'
					]
				}
			]
		},
		options: polarOptions
	});
	topSubsChart = new Chart(ctxSubsBots, {
		type: 'polarArea',
		data: {
			'labels': topSubs.map(sub => { return sub['name']}),
			'datasets': [
				{
					'data': topSubs.map(sub => {return sub['votes']['good'] + sub['votes']['bad']}),
					'backgroundColor': [
						'rgba(0, 255, 0, 1)',
						'rgba(255, 0, 0, 1)',
						'rgba(0, 0, 255, 1)',
						'rgba(255, 255, 0, 1)',
						'rgba(255, 0, 255, 1)'
					]
				}
			]
		},
		options: polarOptions
	});
}

function destroyAllCharts() {
	if (gridChart) {
		gridChart.destroy();
	}
	if (pieChart) {
		pieChart.destroy();
	}
	if (topBotsChart) {
		topBotsChart.destroy();
	}
	if (topSubsChart) {
		topSubsChart.destroy();
	}
}

function loadData(time) {
	let query = `query ($after:String) {
	  bots(after: $after, limit: 5) {
		name
		votes {
		  good
		  bad
		}
	  }
	  graph(after: $after) {
		labels
		votes {
		  good
		  bad
		}
	  }
	  subs(after: $after, limit: 5) {
		name
		votes {
		  good
		  bad
		}
	  }
	  goodStats: stats(after: $after, voteType: GOOD) {
		votes {
		  count
		}
	  }
	  badStats: stats(after: $after, voteType: BAD) {
		votes {
		  count
		}
  	  }
	}`;
	$.ajax({
		url: "/graphql",
		method: "POST",
		contentType: "application/json",
		data: JSON.stringify({
			query: query,
			variables: {
				after: time
			}
		})
	}).done(function( data ) {
        $('#loader').remove();
        destroyAllCharts();
        refreshCharts(data, time);
	});
}

$(function() {
	loadData('1y');

	$('.dropdown-menu a').click(function() {
		let time = $(this).data('value');
		loadData(time);
	});
});
