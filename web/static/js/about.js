$(function() {
	$.ajax({
		url: 'https://raw.githubusercontent.com/Brandawg93/Botranks/master/README.md',
		success(data) {
			let converter = new showdown.Converter(),
				text      = data,
				html      = converter.makeHtml(text);
			$('#loader').remove();
			$('#README').html(html);
		}
	});
});
