function loadData(after, sort) {
	let query = `query ($after:String, $sort:String) {
	  bots(after: $after, sort: $sort) {
		rank
		name
		score
		votes {
		  good
		  bad
		}
		karma {
		  link
		  comment
		}
	  }
	  stats(after: $after) {
		votes {
		  latest
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
				after: after,
				sort: sort
			}
		})
	}).done(function(response) {
		let data = response.data;
		let bots = data['bots'];
		let stats = data['stats'];
		let latestVote = stats['votes']['latest'];
		let voteCount = stats['votes']['count'];
		let lastUpdate = $("#lastUpdate");
		let totalVotes = $("#totalVotes");
		$('#loader').remove();
		$("#updateContainer").show();
		let d = new Date(latestVote * 1000);
		lastUpdate.text("Latest Vote: " + d.toLocaleDateString() + " " + d.toLocaleTimeString())
		totalVotes.text("Total Votes: " + addCommas(voteCount));
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
			data: bots,
			noDataContent: 'Bot not found',
			onRefreshed() {
				if (firstLoad) {
					firstLoad = false;
					searchbar.show();
					let bot = getUrlParameter('bot');
					if (typeof bot !== 'undefined') {
						let rank = bots.find((x) => x['name'] === bot);
						let page = Math.ceil(rank['rank'] / 100);
						if (page > 1) {
							let gridData = grid.data('JSGrid');
							gridData.openPage(page);
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
				let bot = e.item['name'];
				window.open('https://www.reddit.com/u/' + bot);
			},
			fields: [
				{ name: 'rank', title: 'Rank', type: 'number', width: 50 },
				{ name: 'name', title: 'Bot Name', type: 'text', width: 200 },
				{ name: 'score', title: 'Score', type: 'number', width: 75 },
				{ name: 'votes.good', title: 'Good Bot Votes', type: 'number', width: 75 },
				{ name: 'votes.bad', title: 'Bad Bot Votes', type: 'number', width: 75 },
				{ name: 'karma.comment', title: 'Comment Karma', type: 'number', width: 75 },
				{ name: 'karma.link', title: 'Link Karma', type: 'number', width: 75 }
			]
		}).data('JSGrid');

		searchbar.keyup(function() {
			let val = $(this).val();
			let filtered = $.grep( bots, function( rank ) {
				let bot = rank['name'].toLowerCase();
				return bot.startsWith(val.toLowerCase());
			});
			grid.jsGrid('option', 'data', filtered);
		});
	});
}

$(function() {
	loadData('1y');

	$('#dropdownDuration a').click(function() {
		let time = $(this).data('value');
		let sort = $('#dropdownSort .active').data('value');
		loadData(time, sort);
	});

	$('#dropdownSort a').click(function() {
		let time = $('#dropdownDuration .active').data('value');
		let sort = $(this).data('value');
		if (sort === 'hot') {
			$('.dropdown-duration').hide();
		} else {
			$('.dropdown-duration').show();
		}
		loadData(time, sort);
	});
});
