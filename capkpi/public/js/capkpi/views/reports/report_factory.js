// Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

capkpi.views.ReportFactory = class ReportFactory extends capkpi.views.Factory {
	make(route) {
		const _route = ['List', route[1], 'Report'];

		if (route[2]) {
			// custom report
			_route.push(route[2]);
		}

		capkpi.set_route(_route);
	}
}
