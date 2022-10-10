// Copyright (c) 2021, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Form Tour', {
	setup: function(frm) {
		frm.set_query("reference_doctype", function() {
			return {
				filters: {
					istable: 0
				}
			};
		});

		frm.set_query("field", "steps", function() {
			return {
				query: "capkpi.desk.doctype.form_tour.form_tour.get_docfield_list",
				filters: {
					doctype: frm.doc.reference_doctype,
					hidden: 0
				}
			};
		});
	}
});
