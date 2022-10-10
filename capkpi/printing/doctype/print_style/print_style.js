// Copyright (c) 2017, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Print Style', {
	refresh: function(frm) {
		frm.add_custom_button(__('Print Settings'), () => {
			capkpi.set_route('Form', 'Print Settings');
		})
	}
});
