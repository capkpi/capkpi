// Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// for translation
capkpi._ = function(txt, replace, context = null) {
	if (!txt) return txt;
	if (typeof txt != "string") return txt;

	let translated_text = '';

	let key = txt;    // txt.replace(/\n/g, "");
	if (context) {
		translated_text = capkpi._messages[`${key}:${context}`];
	}

	if (!translated_text) {
		translated_text = capkpi._messages[key] || txt;
	}

	if (replace && typeof replace === "object") {
		translated_text = $.format(translated_text, replace);
	}
	return translated_text;
};

window.__ = capkpi._;

capkpi.get_languages = function() {
	if (!capkpi.languages) {
		capkpi.languages = [];
		$.each(capkpi.boot.lang_dict, function(lang, value) {
			capkpi.languages.push({ label: lang, value: value });
		});
		capkpi.languages = capkpi.languages.sort(function(a, b) {
			return a.value < b.value ? -1 : 1;
		});
	}
	return capkpi.languages;
};
