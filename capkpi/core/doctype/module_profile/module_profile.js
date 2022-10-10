// Copyright (c) 2020, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Module Profile', {
	refresh: function(frm) {
		if (has_common(capkpi.user_roles, ["Administrator", "System Manager"])) {
			if (!frm.module_editor && frm.doc.__onload && frm.doc.__onload.all_modules) {
				let module_area = $('<div style="min-height: 300px">')
					.appendTo(frm.fields_dict.module_html.wrapper);

				frm.module_editor = new capkpi.ModuleEditor(frm, module_area);
			}
		}

		if (frm.module_editor) {
			frm.module_editor.refresh();
		}
	}
});