// Copyright (c) 2019, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Notification Settings', {
	onload: (frm) => {
		capkpi.breadcrumbs.add({
			label: __('Settings'),
			route: '#modules/Settings',
			type: 'Custom'
		});
		frm.set_query('subscribed_documents', () => {
			return {
				filters: {
					istable: 0
				}
			};
		});
	},

	refresh: (frm) => {
		if (capkpi.user.has_role('System Manager')) {
			frm.add_custom_button(__('Go to Notification Settings List'), () => {
				capkpi.set_route('List', 'Notification Settings');
			});
		}
	}

});
