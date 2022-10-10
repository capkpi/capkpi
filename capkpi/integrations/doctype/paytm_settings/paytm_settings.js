// Copyright (c) 2020, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Paytm Settings', {
	refresh: function(frm) {
		frm.dashboard.set_headline(__("For more information, {0}.", [`<a href='https://capkpi.com/docs/user/manual/en/erp_integration/paytm-integration'>${__('Click here')}</a>`]));
	}
});
