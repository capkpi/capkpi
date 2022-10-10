capkpi.ui.form.on('Report', {
	refresh: function(frm) {
		if (frm.doc.is_standard === "Yes" && !capkpi.boot.developer_mode) {
			// make the document read-only
			frm.disable_form();
		} else {
			frm.enable_save();
		}

		let doc = frm.doc;
		frm.add_custom_button(__("Show Report"), function() {
			switch(doc.report_type) {
				case "Report Builder":
					capkpi.set_route('List', doc.ref_doctype, 'Report', doc.name);
					break;
				case "Query Report":
					capkpi.set_route("query-report", doc.name);
					break;
				case "Script Report":
					capkpi.set_route("query-report", doc.name);
					break;
				case "Custom Report":
					capkpi.set_route("query-report", doc.name);
					break;
			}
		}, "fa fa-table");

		if (doc.is_standard === "Yes" && frm.perm[0].write) {
			frm.add_custom_button(doc.disabled ? __("Enable Report") : __("Disable Report"), function() {
				frm.call('toggle_disable', {
					disable: doc.disabled ? 0 : 1
				}).then(() => {
					frm.reload_doc();
				});
			}, doc.disabled ? "fa fa-check" : "fa fa-off");
		}
	},

	ref_doctype: function(frm) {
		if(frm.doc.ref_doctype) {
			frm.trigger("set_doctype_roles");
		}
	},

	set_doctype_roles: function(frm) {
		return frm.call('set_doctype_roles').then(() => {
			frm.refresh_field('roles');
		});
	}
})