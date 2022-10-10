// Copyright (c) 2016, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Module Def', {
	refresh: function(frm) {
		capkpi.xcall('capkpi.core.doctype.module_def.module_def.get_installed_apps').then(r => {
			frm.set_df_property('app_name', 'options', JSON.parse(r));
		});
	}
});
