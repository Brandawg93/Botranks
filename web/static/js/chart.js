let gridChart;
let pieChart;
let topBotsChart;
let topSubsChart;

function refreshCharts(data, time) {
	let votes = data['votes'];
	let pie = data['pie'];
	let topBots = data['top_bots'];
	let topSubs = data['top_subs'];
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
		data: votes,
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
		data: pie,
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
		data: topBots,
		options: polarOptions
	});
	topSubsChart = new Chart(ctxSubsBots, {
		type: 'polarArea',
		data: topSubs,
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
	$.getJSON( 'api/getcharts?after=' + time, function( data ) {
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
