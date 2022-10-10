// Copyright (c) 2020, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('System Console', {
	onload: function(frm) {
		capkpi.ui.keys.add_shortcut({
			shortcut: 'shift+enter',
			action: () => frm.execute_action('Execute'),
			page: frm.page,
			description: __('Execute Console script'),
			ignore_inputs: true,
		});
	},

	refresh: function(frm) {
		frm.disable_save();
		frm.page.set_primary_action(__("Execute"), () => {
			frm.execute_action('Execute');
		});
	},
});
