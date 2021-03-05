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

$(function() {
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
