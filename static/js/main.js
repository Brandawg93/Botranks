let getUrlParameter = function getUrlParameter(sParam) {
    let sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[`${i}`].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === 'undefined' ? true : sParameterName[1];
        }
    }
};

function refreshCharts(data) {
	let votes = data['body']['votes'];
	let pie = data['body']['pie'];
	let ctx = document.getElementById('votes').getContext('2d');
	let ctxPie = document.getElementById('votesPie').getContext('2d');
	let myLineChart = new Chart(ctx, {
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
			}
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
}

function refreshREADME() {
	$.ajax({
		url: 'https://raw.githubusercontent.com/Brandawg93/Botranks/master/README.md',
		success(data) {
			let converter = new showdown.Converter(),
				text      = data,
				html      = converter.makeHtml(text);
			$('#README').html(html);
		}
	});
}

function checkAdBlocker() {
	window.onload = function() {
		setTimeout(function() {
			let ad = document.querySelector('ins.adsbygoogle');
			if (ad && ad.innerHTML.replace(/\s/g, '').length === 0) {
				ad.style.cssText = 'display:block !important';
				ad.innerHTML = 'You seem to blocking Google AdSense ads in your browser.';
			}
		}, 2000);
	};
}

function loadData(time, refresh=false) {
	$.getJSON( 'api/getranks?after=' + time, function( data ) {
		$('#grid-loader').remove();
		let statsTab = $('.nav-pills #statsTab');
		statsTab.on('shown.bs.tab', function(){
			refreshCharts(data);
		});
		if (refresh && statsTab.hasClass('active')) {
			refreshCharts(data);
		}
		let ranks = data['body']['ranks'];
		let firstLoad = true;
		$('#ranksGrid').jsGrid({
			width: '100%',
			inserting: false,
			editing: false,
			sorting: true,
			paging: true,
			pageSize: 100,
			data: ranks,
			onRefreshed() {
				if (firstLoad) {
					firstLoad = false;
					let bot = getUrlParameter('bot');
					if (typeof bot !== 'undefined') {
						let rank = ranks.find((x) => x['bot'] === bot);
						let page = Math.ceil(rank['rank'] / 100);
						if (page > 1) {
							let grid = $('#ranksGrid').data('JSGrid');
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
				$('.jsgrid-row, .jsgrid-alt-row').click(function() {
					let bot = $(this).children()[1].innerHTML;
					window.open('https://www.reddit.com/u/' + bot);
				});
			},
			fields: [
				{ name: 'rank', title: 'Rank', type: 'number', width: 50 },
				{ name: 'bot', title: 'Bot Name', type: 'text', width: 150 },
				{ name: 'score', title: 'Score', type: 'number', width: 75 },
				{ name: 'good_bots', title: 'Good Bot Votes', type: 'number', width: 75 },
				{ name: 'bad_bots', title: 'Bad Bot Votes', type: 'number', width: 75 },
				{ name: 'comment_karma', title: 'Comment Karma', type: 'number', width: 75 },
				{ name: 'link_karma', title: 'Link Karma', type: 'number', width: 75 }
			]
		});
	});
}

$(document).ready(function() {
	checkAdBlocker();
	loadData('1y');

	let aboutTab = $('.nav-pills #aboutTab');
	aboutTab.on('shown.bs.tab', function(){
		refreshREADME();
	});

	$('.dropdown-menu a').click(function() {
		$('.dropdown-menu a').removeClass('active');
		$(this).addClass('active');
		let time = $(this).data('value');
		loadData(time, true);
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
