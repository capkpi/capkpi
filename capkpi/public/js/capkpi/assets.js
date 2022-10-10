// Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// library to mange assets (js, css, models, html) etc in the app.
// will try and get from localStorage if latest are available
// depends on capkpi.versions to manage versioning

capkpi.require = function(items, callback) {
	if(typeof items === "string") {
		items = [items];
	}
	return new Promise(resolve => {
		capkpi.assets.execute(items, () => {
			resolve();
			callback && callback();
		});
	});
};

capkpi.assets = {
	check: function() {
		// if version is different then clear localstorage
		if(window._version_number != localStorage.getItem("_version_number")) {
			capkpi.assets.clear_local_storage();
			console.log("Cleared App Cache.");
		}

		if(localStorage._last_load) {
			var not_updated_since = new Date() - new Date(localStorage._last_load);
			if(not_updated_since < 10000 || not_updated_since > 86400000) {
				capkpi.assets.clear_local_storage();
			}
		} else {
			capkpi.assets.clear_local_storage();
		}

		capkpi.assets.init_local_storage();
	},

	init_local_storage: function() {
		localStorage._last_load = new Date();
		localStorage._version_number = window._version_number;
		if(capkpi.boot) localStorage.metadata_version = capkpi.boot.metadata_version;
	},

	clear_local_storage: function() {
		$.each(["_last_load", "_version_number", "metadata_version", "page_info",
			"last_visited"], function(i, key) {
			localStorage.removeItem(key);
		});

		// clear assets
		for(var key in localStorage) {
			if(key.indexOf("desk_assets:")===0 || key.indexOf("_page:")===0
				|| key.indexOf("_doctype:")===0 || key.indexOf("preferred_breadcrumbs:")===0) {
				localStorage.removeItem(key);
			}
		}
		console.log("localStorage cleared");
	},


	// keep track of executed assets
	executed_ : [],

	// pass on to the handler to set
	execute: function(items, callback) {
		var to_fetch = []
		for(var i=0, l=items.length; i<l; i++) {
			if(!capkpi.assets.exists(items[i])) {
				to_fetch.push(items[i]);
			}
		}
		if(to_fetch.length) {
			capkpi.assets.fetch(to_fetch, function() {
				capkpi.assets.eval_assets(items, callback);
			});
		} else {
			capkpi.assets.eval_assets(items, callback);
		}
	},

	eval_assets: function(items, callback) {
		for(var i=0, l=items.length; i<l; i++) {
			// execute js/css if not already.
			var path = items[i];
			if(capkpi.assets.executed_.indexOf(path)===-1) {
				// execute
				capkpi.assets.handler[capkpi.assets.extn(path)](capkpi.assets.get(path), path);
				capkpi.assets.executed_.push(path)
			}
		}
		callback && callback();
	},

	// check if the asset exists in
	// localstorage
	exists: function(src) {
		if(capkpi.assets.executed_.indexOf(src)!== -1) {
			return true;
		}
		if(capkpi.boot.developer_mode) {
			return false;
		}
		if(capkpi.assets.get(src)) {
			return true;
		} else {
			return false;
		}
	},

	// load an asset via
	fetch: function(items, callback) {
		// this is virtual page load, only get the the source
		// *without* the template

		capkpi.call({
			type: "GET",
			method:"capkpi.client.get_js",
			args: {
				"items": items
			},
			callback: function(r) {
				$.each(items, function(i, src) {
					capkpi.assets.add(src, r.message[i]);
				});
				callback();
			},
			freeze: true,
		});
	},

	add: function(src, txt) {
		if('localStorage' in window) {
			try {
				capkpi.assets.set(src, txt);
			} catch(e) {
				// if quota is exceeded, clear local storage and set item
				capkpi.assets.clear_local_storage();
				capkpi.assets.set(src, txt);
			}
		}
	},

	get: function(src) {
		return localStorage.getItem("desk_assets:" + src);
	},

	set: function(src, txt) {
		localStorage.setItem("desk_assets:" + src, txt);
	},

	extn: function(src) {
		if(src.indexOf('?')!=-1) {
			src = src.split('?').slice(-1)[0];
		}
		return src.split('.').slice(-1)[0];
	},

	handler: {
		js: function(txt, src) {
			capkpi.dom.eval(txt);
		},
		css: function(txt, src) {
			capkpi.dom.set_style(txt);
		}
	},

	include_style(file, base_url, is_rtl=null) {
		let path = `${base_url}/assets/css/${file}`;
		if (is_rtl) {
			path = `${base_url}/assets/css-rtl/${file}`;
		}
		return `<link href="${path}" rel="stylesheet">`;
	}
};
