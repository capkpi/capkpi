// Copyright (c) 2019, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Document Type Mapping', {
	local_doctype: function(frm) {
		if (frm.doc.local_doctype) {
			capkpi.model.clear_table(frm.doc, 'field_mapping');
			let fields = frm.events.get_fields(frm);
			$.each(fields, function(i, data) {
				let row = capkpi.model.add_child(frm.doc, 'Document Type Field Mapping', 'field_mapping');
				row.local_fieldname = data;
			});
			refresh_field('field_mapping');
		}
	},

	get_fields: function(frm) {
		let filtered_fields = [];
		capkpi.model.with_doctype(frm.doc.local_doctype, ()=> {
			capkpi.get_meta(frm.doc.local_doctype).fields.map( field => {
				if (field.fieldname !== 'remote_docname' && field.fieldname !== 'remote_site_name' && capkpi.model.is_value_type(field) && !field.hidden) {
					filtered_fields.push(field.fieldname);
				}
			});
		});
		return filtered_fields;
	}
});
