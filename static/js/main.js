$(document).ready(function() {
	$.getJSON( "api/getranks?after=1d", function( data ) {
		let votes = data['body']['votes'];
		let ctx = document.getElementById('votes').getContext('2d');
		let myLineChart = new Chart(ctx, {
			type: 'line',
			data: votes,
			options: {
			  responsive: true,
			  maintainAspectRatio: false
			}
		});
	});
});
