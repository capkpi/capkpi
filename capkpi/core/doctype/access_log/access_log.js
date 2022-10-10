// Copyright (c) 2019, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Access Log', {
	show_document: function (frm) {
		capkpi.set_route('Form', frm.doc.export_from, frm.doc.reference_document);
	},

	show_report: function (frm) {
		if (frm.doc.report_name.includes('/')) {
			capkpi.set_route(frm.doc.report_name);
		} else {
			let filters = frm.doc.filters ? JSON.parse(frm.doc.filters) : {};
			capkpi.set_route('query-report', frm.doc.report_name, filters);
		}
	}
});
