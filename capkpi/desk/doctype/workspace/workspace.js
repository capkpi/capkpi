// Copyright (c) 2020, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Workspace', {
	setup: function() {
		capkpi.meta.get_field('Workspace Link', 'only_for').no_default = true;
	},

	refresh: function(frm) {
		frm.enable_save();
		frm.get_field("is_standard").toggle(capkpi.boot.developer_mode);
		frm.get_field("developer_mode_only").toggle(capkpi.boot.developer_mode);

		if (frm.doc.for_user) {
			frm.set_df_property("extends", "read_only", true);
		}

		if (frm.doc.for_user || (frm.doc.is_standard && !capkpi.boot.developer_mode)) {
			frm.trigger('disable_form');
		}
	},

	disable_form: function(frm) {
		frm.fields
			.filter(field => field.has_input)
			.forEach(field => {
				frm.set_df_property(field.df.fieldname, "read_only", "1");
			});
		frm.disable_save();
	}
});