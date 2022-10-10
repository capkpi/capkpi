// Copyright (c) 2017, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Data Migration Plan', {
	onload(frm) {
		frm.add_custom_button(__('Run'), () => capkpi.new_doc('Data Migration Run', {
			data_migration_plan: frm.doc.name
		}));
	}
});
