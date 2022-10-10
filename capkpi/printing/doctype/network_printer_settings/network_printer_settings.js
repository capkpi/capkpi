// Copyright (c) 2021, CapKPI Technologies and contributors
// For license information, please see license.txt

capkpi.ui.form.on('Network Printer Settings', {
	onload (frm) {
		frm.trigger("connect_print_server");
	},
	server_ip (frm) {
		frm.trigger("connect_print_server");
	},
	port (frm) {
		frm.trigger("connect_print_server");
	},
	connect_print_server (frm) {
		if (frm.doc.server_ip && frm.doc.port) {
			capkpi.call({
				"doc": frm.doc,
				"method": "get_printers_list",
				"args": {
					ip: frm.doc.server_ip,
					port: frm.doc.port
				},
				callback: function(data) {
					frm.set_df_property('printer_name', 'options', [""].concat(data.message));
				}
			});
		}
	}
});
