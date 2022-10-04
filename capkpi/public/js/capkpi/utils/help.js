// Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

capkpi.provide("capkpi.help");

capkpi.help.youtube_id = {};

capkpi.help.has_help = function (doctype) {
	return capkpi.help.youtube_id[doctype];
}

capkpi.help.show = function (doctype) {
	if (capkpi.help.youtube_id[doctype]) {
		capkpi.help.show_video(capkpi.help.youtube_id[doctype]);
	}
}

capkpi.help.show_video = function (youtube_id, title) {
	if (capkpi.utils.is_url(youtube_id)) {
		const expression = '(?:youtube.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu.be/)([^"&?\\s]{11})';
		youtube_id = youtube_id.match(expression)[1];
	}

	// (capkpi.help_feedback_link || "")
	let dialog = new capkpi.ui.Dialog({
		title: title || __("Help"),
		size: 'large'
	});

	let video = $(`<div class="video-player" data-plyr-provider="youtube" data-plyr-embed-id="${youtube_id}"></div>`);
	video.appendTo(dialog.body);

	dialog.show();
	dialog.$wrapper.addClass("video-modal");

	let plyr = new capkpi.Plyr(video[0], {
		hideControls: true,
		resetOnEnd: true,
	});

	dialog.onhide = () => {
		plyr.destroy();
	};
}

$("body").on("click", "a.help-link", function () {
	var doctype = $(this).attr("data-doctype");
	doctype && capkpi.help.show(doctype);
});
