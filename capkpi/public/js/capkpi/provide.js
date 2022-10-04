// Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// provide a namespace
if(!window.capkpi)
	window.capkpi = {};

capkpi.provide = function(namespace) {
	// docs: create a namespace //
	var nsl = namespace.split('.');
	var parent = window;
	for(var i=0; i<nsl.length; i++) {
		var n = nsl[i];
		if(!parent[n]) {
			parent[n] = {}
		}
		parent = parent[n];
	}
	return parent;
}

capkpi.provide("locals");
capkpi.provide("capkpi.flags");
capkpi.provide("capkpi.settings");
capkpi.provide("capkpi.utils");
capkpi.provide("capkpi.ui.form");
capkpi.provide("capkpi.modules");
capkpi.provide("capkpi.templates");
capkpi.provide("capkpi.test_data");
capkpi.provide('capkpi.utils');
capkpi.provide('capkpi.model');
capkpi.provide('capkpi.user');
capkpi.provide('capkpi.session');
capkpi.provide("capkpi._messages");
capkpi.provide('locals.DocType');

// for listviews
capkpi.provide("capkpi.listview_settings");
capkpi.provide("capkpi.tour");
capkpi.provide("capkpi.listview_parent_route");

// constants
window.NEWLINE = '\n';
window.TAB = 9;
window.UP_ARROW = 38;
window.DOWN_ARROW = 40;

// proxy for user globals defined in desk.js

// API globals
window.cur_frm=null;
