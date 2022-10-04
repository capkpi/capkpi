// Copyright (c) 2019, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on("Personal Data Deletion Request", {
	refresh: function(frm) {
		if (
			capkpi.user.has_role("System Manager") &&
			frm.doc.status == "Pending Approval"
		) {
			frm.add_custom_button(__("Delete Data"), function() {
				return capkpi.call({
					doc: frm.doc,
					method: "trigger_data_deletion",
					freeze: true,
					callback: function() {
						frm.refresh();
					}
				});
			});
		}
	}
});
