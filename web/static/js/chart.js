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
		let weekday = new Array(7);
		weekday[0] = 'Sunday';
		weekday[1] = 'Monday';
		weekday[2] = 'Tuesday';
		weekday[3] = 'Wednesday';
		weekday[4] = 'Thursday';
		weekday[5] = 'Friday';
		weekday[6] = 'Saturday';
		linePoint = weekday[d.getDay()];
	} else if (time.indexOf('M') > -1) {
		linePoint = new Date().getDate();
	} else if (time.indexOf('y') > -1) {
		let d = new Date();
		let month = new Array(12);
		month[0] = 'January';
		month[1] = 'February';
		month[2] = 'March';
		month[3] = 'April';
		month[4] = 'May';
		month[5] = 'June';
		month[6] = 'July';
		month[6] = 'August';
		month[6] = 'September';
		month[6] = 'October';
		month[6] = 'November';
		month[6] = 'December';
		linePoint = month[d.getMonth()];
	}
	new Chart(ctx, {
		type: 'line',
		data: votes,
		options: {
			responsive: true,
			maintainAspectRatio: false,
			scales: {
				xAxes: [{
					gridLines: {
						color: '#d9d9d9'
					},
					scaleLabel: {
						display: true,
						labelString: 'Timeline'
					}
				}],
				yAxes: [{
					gridLines: {
						color: '#d9d9d9'
					},
					scaleLabel: {
						display: true,
						labelString: 'Number of Votes'
					}
				}]
			},
			annotation: {
				annotations: [
					{
						type: 'line',
						mode: 'vertical',
						scaleID: 'x-axis-0',
						value: linePoint,
						borderColor: 'red',
						label: {
							content: 'Now',
							enabled: true,
							position: 'top'
						}
					}
				]
			}
		}
	});
	new Chart(ctxPie, {
		type: 'doughnut',
		data: pie,
		options: {
			responsive: true,
			maintainAspectRatio: false
		}
	});
	let polarOptions = {
			scale: {
				gridLines: {
					color: '#d9d9d9'
				}
			},
			responsive: true,
			maintainAspectRatio: false
		};
	new Chart(ctxTopBots, {
		type: 'polarArea',
		data: topBots,
		options: polarOptions
	});
	new Chart(ctxSubsBots, {
		type: 'polarArea',
		data: topSubs,
		options: polarOptions
	});
}

function loadData(time) {
	$.getJSON( 'api/getcharts?after=' + time, function( data ) {
        $('#loader').remove();
        refreshCharts(data, time);
	});
}

$(function() {
	loadData('1y');

	$('.dropdown-menu a').click(function() {
		$('.dropdown-menu a').removeClass('active');
		$(this).addClass('active');
		let time = $(this).data('value');
		loadData(time, true);
	});
});
