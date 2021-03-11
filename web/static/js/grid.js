function loadData(time) {
	$.getJSON('api/getranks?after=' + time, function( ranks ) {
		$('#loader').remove();
		$("#lastUpdate").show();
		let firstLoad = true;
		let grid = $('#ranksGrid');
		let searchbar = $('.searchbar');
		grid.jsGrid({
			width: '100%',
			inserting: false,
			editing: false,
			sorting: true,
			paging: true,
			pageSize: 100,
			pageButtonCount: 3,
			data: ranks,
			noDataContent: 'Bot not found',
			onRefreshed() {
				if (firstLoad) {
					firstLoad = false;
					searchbar.show();
					let bot = getUrlParameter('bot');
					if (typeof bot !== 'undefined') {
						let rank = ranks.find((x) => x['bot'] === bot);
						let page = Math.ceil(rank['rank'] / 100);
						if (page > 1) {
							let grid = grid.data('JSGrid');
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
			rowClick(e) {
				let bot = e.item.bot;
				window.open('https://www.reddit.com/u/' + bot);
			},
			fields: [
				{ name: 'rank', title: 'Rank', type: 'number', width: 50 },
				{ name: 'bot', title: 'Bot Name', type: 'text', width: 200 },
				{ name: 'score', title: 'Score', type: 'number', width: 75 },
				{ name: 'good_bots', title: 'Good Bot Votes', type: 'number', width: 75 },
				{ name: 'bad_bots', title: 'Bad Bot Votes', type: 'number', width: 75 },
				{ name: 'comment_karma', title: 'Comment Karma', type: 'number', width: 75 },
				{ name: 'link_karma', title: 'Link Karma', type: 'number', width: 75 }
			]
		}).data('JSGrid');

		searchbar.keyup(function() {
			let val = $(this).val();
			let filtered = $.grep( ranks, function( rank, i ) {
				let bot = rank.bot.toLowerCase();
				return bot.startsWith(val.toLowerCase());
			});
			grid.jsGrid('option', 'data', filtered);
		});
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

	$.getJSON('api/getlastupdate', function(data) {
		let d = new Date(data * 1000);
		$("#lastUpdate").text("Latest Vote: " + d.toLocaleDateString() + " " + d.toLocaleTimeString())
	});
});
