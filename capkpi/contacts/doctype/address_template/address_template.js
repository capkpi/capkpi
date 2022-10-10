// Copyright (c) 2016, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Address Template', {
	refresh: function(frm) {
		if(frm.is_new() && !frm.doc.template) {
			// set default template via js so that it is translated
			capkpi.call({
				method: 'capkpi.contacts.doctype.address_template.address_template.get_default_address_template',
				callback: function(r) {
					frm.set_value('template', r.message);
				}
			});
		}
	}
});
