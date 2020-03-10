$(document).ready(function() {
	$.getJSON( 'api/getranks?after=1d', function( data ) {
		$('#grid-loader').remove();
		let votes = data['body']['votes'];
		let pie = data['body']['pie'];
		let ranks = data['body']['ranks'];
		$('.nav-pills #statsTab').on('shown.bs.tab', function(){
			let ctx = document.getElementById('votes').getContext('2d');
			let ctxPie = document.getElementById('votesPie').getContext('2d');
			let myLineChart = new Chart(ctx, {
				type: 'line',
				data: votes,
				options: {
					responsive: true,
					maintainAspectRatio: false
				}
			});
			let myDoughnutChart = new Chart(ctxPie, {
				type: 'doughnut',
				data: pie,
				options: {
					responsive: true,
					maintainAspectRatio: false
				}
			});
		});

		$('#ranksGrid').jsGrid({
			width: '100%',
			inserting: false,
			editing: false,
			sorting: true,
			paging: true,
			pageSize: 100,
			data: ranks,
			fields: [
				{ name: 'rank', title: 'Rank', type: 'number', width: 50 },
				{ name: 'bot', title: 'Bot Name', type: 'text', width: 150 },
				{ name: 'score', title: 'Score', type: 'number', width: 75 },
				{ name: 'good_bots', title: 'Good Bot Votes', type: 'number', width: 75 },
				{ name: 'bad_bots', title: 'Bad Bot Votes', type: 'number', width: 75 }
			]
		});
	});
});
