capkpi.listview_settings['Event'] = {
	add_fields: ["starts_on", "ends_on"],
	onload: function() {
		capkpi.route_options = {
			"status": "Open"
		};
	}
}