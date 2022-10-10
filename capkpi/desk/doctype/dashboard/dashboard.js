// Copyright (c) 2019, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Dashboard', {
	refresh: function(frm) {
		frm.add_custom_button(__("Show Dashboard"),
			() => capkpi.set_route('dashboard-view', frm.doc.name)
		);

		if (!capkpi.boot.developer_mode && frm.doc.is_standard) {
			frm.disable_form();
		}

		frm.set_query("chart", "charts", function() {
			return {
				filters: {
					is_public: 1,
				}
			};
		});

		frm.set_query("card", "cards", function() {
			return {
				filters: {
					is_public: 1,
				}
			};
		});
	}
});