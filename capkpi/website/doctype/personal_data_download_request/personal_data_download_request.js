// Copyright (c) 2019, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Personal Data Download Request', {
	onload: function(frm) {
		if (frm.is_new()) {
			frm.doc.user = capkpi.session.user;
		}
	},
});
