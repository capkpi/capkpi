// Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

capkpi.ui.form.on('Role', {
	refresh: function(frm) {
		frm.set_df_property('is_custom', 'read_only', capkpi.session.user !== 'Administrator');

		frm.add_custom_button("Role Permissions Manager", function() {
			capkpi.route_options = {"role": frm.doc.name};
			capkpi.set_route("permission-manager");
		});
		frm.add_custom_button("Show Users", function() {
			capkpi.route_options = {"role": frm.doc.name};
			capkpi.set_route("List", "User", "Report");
		});
	}
});
