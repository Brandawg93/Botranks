let getUrlParameter = function getUrlParameter(sParam) {
    let sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
};

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

		let firstLoad = true;
		$('#ranksGrid').jsGrid({
			width: '100%',
			inserting: false,
			editing: false,
			sorting: true,
			paging: true,
			pageSize: 100,
			data: ranks,
			onRefreshed: function() {
				if (firstLoad) {
					firstLoad = false;
					let bot = getUrlParameter('bot');
					if (typeof bot !== 'undefined') {
						let rank = ranks.find(x => x['bot'] === bot);
						let page = Math.ceil(rank['rank'] / 100);
						if (page > 1) {
							let grid = $("#ranksGrid").data("JSGrid");
							grid.openPage(page);
						}
						let cell = $('td:contains(\'' + bot + '\')');
						if (cell.length !== 0) {
							let rowpos = cell.position();
							$('body').scrollTop(rowpos.top);
							cell.parent().addClass('jsgrid-selected-row');
						}
					}
				}
			},
			fields: [
				{ name: 'rank', title: 'Rank', type: 'number', width: 50 },
				{ name: 'bot', title: 'Bot Name', type: 'text', width: 150 },
				{ name: 'score', title: 'Score', type: 'number', width: 75 },
				{ name: 'good_bots', title: 'Good Bot Votes', type: 'number', width: 75 },
				{ name: 'bad_bots', title: 'Bad Bot Votes', type: 'number', width: 75 }
			]
		});
	});

	$(window).scroll(function () {
		if ($(this).scrollTop() > 50) {
			$('#back-to-top').fadeIn();
		} else {
			$('#back-to-top').fadeOut();
		}
	});
	// scroll body to 0px on click
	let top = $('#back-to-top');
	top.click(function () {
		$('body,html').animate({
			scrollTop: 0
		}, 800);
		return false;
	});
});
