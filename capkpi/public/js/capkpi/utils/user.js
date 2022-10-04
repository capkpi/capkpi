capkpi.user_info = function(uid) {
	if(!uid)
		uid = capkpi.session.user;

	if(uid.toLowerCase()==="bot") {
		return {
			fullname: __("Bot"),
			image: "/assets/capkpi/images/ui/bot.png",
			abbr: "B"
		};
	}

	if(!(capkpi.boot.user_info && capkpi.boot.user_info[uid])) {
		var user_info = {fullname: uid || "Unknown"};
	} else {
		var user_info = capkpi.boot.user_info[uid];
	}

	user_info.abbr = capkpi.get_abbr(user_info.fullname);
	user_info.color = capkpi.get_palette(user_info.fullname);

	return user_info;
};

capkpi.ui.set_user_background = function(src, selector, style) {
	if(!selector) selector = "#page-desktop";
	if(!style) style = "Fill Screen";
	if(src) {
		if (window.cordova && src.indexOf("http") === -1) {
			src = capkpi.base_url + src;
		}
		var background = repl('background: url("%(src)s") center center;', {src: src});
	} else {
		var background = "background-color: #4B4C9D;";
	}

	capkpi.dom.set_style(repl('%(selector)s { \
		%(background)s \
		background-attachment: fixed; \
		%(style)s \
	}', {
		selector:selector,
		background:background,
		style: style==="Fill Screen" ? "background-size: cover;" : ""
	}));
};

capkpi.provide('capkpi.user');

$.extend(capkpi.user, {
	name: 'Guest',
	full_name: function(uid) {
		return uid === capkpi.session.user ?
			__("You", null, "Name of the current user. For example: You edited this 5 hours ago.") :
			capkpi.user_info(uid).fullname;
	},
	image: function(uid) {
		return capkpi.user_info(uid).image;
	},
	abbr: function(uid) {
		return capkpi.user_info(uid).abbr;
	},
	has_role: function(rl) {
		if(typeof rl=='string')
			rl = [rl];
		for(var i in rl) {
			if((capkpi.boot ? capkpi.boot.user.roles : ['Guest']).indexOf(rl[i])!=-1)
				return true;
		}
	},
	get_desktop_items: function() {
		// hide based on permission
		var modules_list = $.map(capkpi.boot.allowed_modules, function(icon) {
			var m = icon.module_name;
			var type = capkpi.modules[m] && capkpi.modules[m].type;

			if(capkpi.boot.user.allow_modules.indexOf(m) === -1) return null;

			var ret = null;
			if (type === "module") {
				if(capkpi.boot.user.allow_modules.indexOf(m)!=-1 || capkpi.modules[m].is_help)
					ret = m;
			} else if (type === "page") {
				if(capkpi.boot.allowed_pages.indexOf(capkpi.modules[m].link)!=-1)
					ret = m;
			} else if (type === "list") {
				if(capkpi.model.can_read(capkpi.modules[m]._doctype))
					ret = m;
			} else if (type === "view") {
				ret = m;
			} else if (type === "setup") {
				if(capkpi.user.has_role("System Manager") || capkpi.user.has_role("Administrator"))
					ret = m;
			} else {
				ret = m;
			}

			return ret;
		});

		return modules_list;
	},

	is_report_manager: function() {
		return capkpi.user.has_role(['Administrator', 'System Manager', 'Report Manager']);
	},

	get_formatted_email: function(email) {
		var fullname = capkpi.user.full_name(email);

		if (!fullname) {
			return email;
		} else {
			// to quote or to not
			var quote = '';

			// only if these special characters are found
			// why? To make the output same as that in python!
			if (fullname.search(/[\[\]\\()<>@,:;".]/) !== -1) {
				quote = '"';
			}

			return repl('%(quote)s%(fullname)s%(quote)s <%(email)s>', {
				fullname: fullname,
				email: email,
				quote: quote
			});
		}
	},

	get_emails: ( ) => {
		return Object.keys(capkpi.boot.user_info).map(key => capkpi.boot.user_info[key].email);
	},

	/* Normally capkpi.user is an object
	 * having properties and methods.
	 * But in the following case
	 *
	 * if (capkpi.user === 'Administrator')
	 *
	 * capkpi.user will cast to a string
	 * returning capkpi.user.name
	 */
	toString: function() {
		return this.name;
	}
});

capkpi.session_alive = true;
$(document).bind('mousemove', function() {
	if(capkpi.session_alive===false) {
		$(document).trigger("session_alive");
	}
	capkpi.session_alive = true;
	if(capkpi.session_alive_timeout)
		clearTimeout(capkpi.session_alive_timeout);
	capkpi.session_alive_timeout = setTimeout('capkpi.session_alive=false;', 30000);
});