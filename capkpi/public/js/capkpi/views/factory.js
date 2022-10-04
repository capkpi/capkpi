// Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

capkpi.provide('capkpi.pages');
capkpi.provide('capkpi.views');

capkpi.views.Factory = class Factory {
	constructor(opts) {
		$.extend(this, opts);
	}

	show() {
		var page_name = capkpi.get_route_str(),
			me = this;

		if (capkpi.pages[page_name]) {
			capkpi.container.change_to(page_name);
			if(me.on_show) {
				me.on_show();
			}
		} else {
			var route = capkpi.get_route();
			if(route[1]) {
				me.make(route);
			} else {
				capkpi.show_not_found(route);
			}
		}
	}

	make_page(double_column, page_name) {
		return capkpi.make_page(double_column, page_name);
	}
}

capkpi.make_page = function(double_column, page_name) {
	if(!page_name) {
		var page_name = capkpi.get_route_str();
	}
	var page = capkpi.container.add_page(page_name);

	capkpi.ui.make_app_page({
		parent: page,
		single_column: !double_column
	});
	capkpi.container.change_to(page_name);
	return page;
}
