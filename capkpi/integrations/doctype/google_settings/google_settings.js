// Copyright (c) 2019, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Google Settings', {
	refresh: function(frm) {
		frm.dashboard.set_headline(__("For more information, {0}.", [`<a href='https://capkpi.com/docs/user/manual/en/erp_integration/google_settings'>${__('Click here')}</a>`]));
	}
});
