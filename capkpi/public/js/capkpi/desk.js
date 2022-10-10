// Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt
/* eslint-disable no-console */

// __('Modules') __('Domains') __('Places') __('Administration') # for translation, don't remove

capkpi.start_app = function() {
	if (!capkpi.Application)
		return;
	capkpi.assets.check();
	capkpi.provide('capkpi.app');
	capkpi.provide('capkpi.desk');
	capkpi.app = new capkpi.Application();
};

$(document).ready(function() {
	if (!capkpi.utils.supportsES6) {
		capkpi.msgprint({
			indicator: 'red',
			title: __('Browser not supported'),
			message: __('Some of the features might not work in your browser. Please update your browser to the latest version.')
		});
	}
	capkpi.start_app();
});

capkpi.Application = Class.extend({
	init: function() {
		this.startup();
	},

	startup: function() {
		capkpi.socketio.init();
		capkpi.model.init();

		if(capkpi.boot.status==='failed') {
			capkpi.msgprint({
				message: capkpi.boot.error,
				title: __('Session Start Failed'),
				indicator: 'red',
			});
			throw 'boot failed';
		}

		this.setup_capkpi_vue();
		this.load_bootinfo();
		this.load_user_permissions();
		this.make_nav_bar();
		this.set_favicon();
		this.setup_analytics();
		this.set_fullwidth_if_enabled();
		this.add_browser_class();
		this.setup_energy_point_listeners();
		this.setup_copy_doc_listener();

		capkpi.ui.keys.setup();

		capkpi.ui.keys.add_shortcut({
			shortcut: 'shift+ctrl+g',
			description: __('Switch Theme'),
			action: () => {
				capkpi.theme_switcher = new capkpi.ui.ThemeSwitcher();
				capkpi.theme_switcher.show();
			}
		});

		// page container
		this.make_page_container();
		this.set_route();

		// trigger app startup
		$(document).trigger('startup');

		$(document).trigger('app_ready');

		if (capkpi.boot.messages) {
			capkpi.msgprint(capkpi.boot.messages);
		}

		if (capkpi.user_roles.includes('System Manager')) {
			// delayed following requests to make boot faster
			setTimeout(() => {
				this.show_change_log();
				this.show_update_available();
			}, 1000);
		}

		if (!capkpi.boot.developer_mode) {
			let console_security_message = __("Using this console may allow attackers to impersonate you and steal your information. Do not enter or paste code that you do not understand.");
			console.log(
				`%c${console_security_message}`,
				"font-size: large"
			);
		}

		this.show_notes();

		if (capkpi.ui.startup_setup_dialog && !capkpi.boot.setup_complete) {
			capkpi.ui.startup_setup_dialog.pre_show();
			capkpi.ui.startup_setup_dialog.show();
		}

		capkpi.realtime.on("version-update", function() {
			var dialog = capkpi.msgprint({
				message:__("The application has been updated to a new version, please refresh this page"),
				indicator: 'green',
				title: __('Version Updated')
			});
			dialog.set_primary_action(__("Refresh"), function() {
				location.reload(true);
			});
			dialog.get_close_btn().toggle(false);
		});

		// listen to build errors
		this.setup_build_error_listener();

		if (capkpi.sys_defaults.email_user_password) {
			var email_list =  capkpi.sys_defaults.email_user_password.split(',');
			for (var u in email_list) {
				if (email_list[u]===capkpi.user.name) {
					this.set_password(email_list[u]);
				}
			}
		}

		// REDESIGN-TODO: Fix preview popovers
		this.link_preview = new capkpi.ui.LinkPreview();

		if (!capkpi.boot.developer_mode) {
			setInterval(function() {
				capkpi.call({
					method: 'capkpi.core.page.background_jobs.background_jobs.get_scheduler_status',
					callback: function(r) {
						if (r.message[0] == __("Inactive")) {
							capkpi.call('capkpi.utils.scheduler.activate_scheduler');
						}
					}
				});
			}, 300000); // check every 5 minutes

			if (capkpi.user.has_role("System Manager")) {
				setInterval(function() {
					capkpi.call({
						method: 'capkpi.core.doctype.log_settings.log_settings.has_unseen_error_log',
						args: {
							user: capkpi.session.user
						},
						callback: function(r) {
							if (r.message.show_alert) {
								capkpi.show_alert({
									indicator: 'red',
									message: r.message.message
								});
							}
						}
					});
				}, 600000); // check every 10 minutes
			}
		}
	},

	set_route() {
		capkpi.flags.setting_original_route = true;
		if (capkpi.boot && localStorage.getItem("session_last_route")) {
			capkpi.set_route(localStorage.getItem("session_last_route"));
			localStorage.removeItem("session_last_route");
		} else {
			// route to home page
			capkpi.router.route();
		}
		capkpi.after_ajax(() => capkpi.flags.setting_original_route = false);
		capkpi.router.on('change', () => {
			$(".tooltip").hide();
		});
	},

	setup_capkpi_vue() {
		Vue.prototype.__ = window.__;
		Vue.prototype.capkpi = window.capkpi;
	},

	set_password: function(user) {
		var me=this;
		capkpi.call({
			method: 'capkpi.core.doctype.user.user.get_email_awaiting',
			args: {
				"user": user
			},
			callback: function(email_account) {
				email_account = email_account["message"];
				if (email_account) {
					var i = 0;
					if (i < email_account.length) {
						me.email_password_prompt( email_account, user, i);
					}
				}
			}
		});
	},

	email_password_prompt: function(email_account,user,i) {
		var me = this;
		const email_id = email_account[i]["email_id"];
		let d = new capkpi.ui.Dialog({
			title: __('Password missing in Email Account'),
			fields: [
				{
					'fieldname': 'password',
					'fieldtype': 'Password',
					'label': __('Please enter the password for: <b>{0}</b>', [email_id], "Email Account"),
					'reqd': 1
				},
				{
					"fieldname": "submit",
					"fieldtype": "Button",
					"label": __("Submit", null, "Submit password for Email Account")
				}
			]
		});
		d.get_input("submit").on("click", function() {
			//setup spinner
			d.hide();
			var s = new capkpi.ui.Dialog({
				title: __("Checking one moment"),
				fields: [{
					"fieldtype": "HTML",
					"fieldname": "checking"
				}]
			});
			s.fields_dict.checking.$wrapper.html('<i class="fa fa-spinner fa-spin fa-4x"></i>');
			s.show();
			capkpi.call({
				method: 'capkpi.email.doctype.email_account.email_account.set_email_password',
				args: {
					"email_account": email_account[i]["email_account"],
					"user": user,
					"password": d.get_value("password")
				},
				callback: function(passed) {
					s.hide();
					d.hide();//hide waiting indication
					if (!passed["message"]) {
						capkpi.show_alert({message: __("Login Failed please try again"), indicator: 'error'}, 5);
						me.email_password_prompt(email_account, user, i);
					} else {
						if (i + 1 < email_account.length) {
							i = i + 1;
							me.email_password_prompt(email_account, user, i);
						}
					}

				}
			});
		});
		d.show();
	},
	load_bootinfo: function() {
		if(capkpi.boot) {
			this.setup_workspaces();
			capkpi.model.sync(capkpi.boot.docs);
			this.check_metadata_cache_status();
			this.set_globals();
			this.sync_pages();
			capkpi.router.setup();
			this.setup_moment();
			if(capkpi.boot.print_css) {
				capkpi.dom.set_style(capkpi.boot.print_css, "print-style");
			}
			capkpi.user.name = capkpi.boot.user.name;
			capkpi.router.setup();
		} else {
			this.set_as_guest();
		}
	},

	setup_workspaces() {
		capkpi.modules = {};
		capkpi.workspaces = {};
		for (let page of capkpi.boot.allowed_workspaces || []) {
			capkpi.modules[page.module]=page;
			capkpi.workspaces[capkpi.router.slug(page.name)] = page;
		}
		if (!capkpi.workspaces['home']) {
			// default workspace is settings for CapKPI
			capkpi.workspaces['home'] = capkpi.workspaces[Object.keys(capkpi.workspaces)[0]];
		}
	},

	load_user_permissions: function() {
		capkpi.defaults.update_user_permissions();

		capkpi.realtime.on('update_user_permissions', capkpi.utils.debounce(() => {
			capkpi.defaults.update_user_permissions();
		}, 500));
	},

	check_metadata_cache_status: function() {
		if(capkpi.boot.metadata_version != localStorage.metadata_version) {
			capkpi.assets.clear_local_storage();
			capkpi.assets.init_local_storage();
		}
	},

	set_globals: function() {
		capkpi.session.user = capkpi.boot.user.name;
		capkpi.session.logged_in_user = capkpi.boot.user.name;
		capkpi.session.user_email = capkpi.boot.user.email;
		capkpi.session.user_fullname = capkpi.user_info().fullname;

		capkpi.user_defaults = capkpi.boot.user.defaults;
		capkpi.user_roles = capkpi.boot.user.roles;
		capkpi.sys_defaults = capkpi.boot.sysdefaults;

		capkpi.ui.py_date_format = capkpi.boot.sysdefaults.date_format.replace('dd', '%d').replace('mm', '%m').replace('yyyy', '%Y');
		capkpi.boot.user.last_selected_values = {};

		// Proxy for user globals
		Object.defineProperties(window, {
			'user': {
				get: function() {
					console.warn('Please use `capkpi.session.user` instead of `user`. It will be deprecated soon.');
					return capkpi.session.user;
				}
			},
			'user_fullname': {
				get: function() {
					console.warn('Please use `capkpi.session.user_fullname` instead of `user_fullname`. It will be deprecated soon.');
					return capkpi.session.user;
				}
			},
			'user_email': {
				get: function() {
					console.warn('Please use `capkpi.session.user_email` instead of `user_email`. It will be deprecated soon.');
					return capkpi.session.user_email;
				}
			},
			'user_defaults': {
				get: function() {
					console.warn('Please use `capkpi.user_defaults` instead of `user_defaults`. It will be deprecated soon.');
					return capkpi.user_defaults;
				}
			},
			'roles': {
				get: function() {
					console.warn('Please use `capkpi.user_roles` instead of `roles`. It will be deprecated soon.');
					return capkpi.user_roles;
				}
			},
			'sys_defaults': {
				get: function() {
					console.warn('Please use `capkpi.sys_defaults` instead of `sys_defaults`. It will be deprecated soon.');
					return capkpi.user_roles;
				}
			}
		});
	},
	sync_pages: function() {
		// clear cached pages if timestamp is not found
		if(localStorage["page_info"]) {
			capkpi.boot.allowed_pages = [];
			var page_info = JSON.parse(localStorage["page_info"]);
			$.each(capkpi.boot.page_info, function(name, p) {
				if(!page_info[name] || (page_info[name].modified != p.modified)) {
					delete localStorage["_page:" + name];
				}
				capkpi.boot.allowed_pages.push(name);
			});
		} else {
			capkpi.boot.allowed_pages = Object.keys(capkpi.boot.page_info);
		}
		localStorage["page_info"] = JSON.stringify(capkpi.boot.page_info);
	},
	set_as_guest: function() {
		capkpi.session.user = 'Guest';
		capkpi.session.user_email = '';
		capkpi.session.user_fullname = 'Guest';

		capkpi.user_defaults = {};
		capkpi.user_roles = ['Guest'];
		capkpi.sys_defaults = {};
	},
	make_page_container: function() {
		if ($("#body").length) {
			$(".splash").remove();
			capkpi.temp_container = $("<div id='temp-container' style='display: none;'>")
				.appendTo("body");
			capkpi.container = new capkpi.views.Container();
		}
	},
	make_nav_bar: function() {
		// toolbar
		if(capkpi.boot && capkpi.boot.home_page!=='setup-wizard') {
			capkpi.capkpi_toolbar = new capkpi.ui.toolbar.Toolbar();
		}

	},
	logout: function() {
		var me = this;
		me.logged_out = true;
		return capkpi.call({
			method:'logout',
			callback: function(r) {
				if(r.exc) {
					return;
				}
				me.redirect_to_login();
			}
		});
	},
	handle_session_expired: function() {
		if(!capkpi.app.session_expired_dialog) {
			var dialog = new capkpi.ui.Dialog({
				title: __('Session Expired'),
				keep_open: true,
				fields: [
					{ fieldtype:'Password', fieldname:'password',
						label: __('Please Enter Your Password to Continue') },
				],
				onhide: () => {
					if (!dialog.logged_in) {
						capkpi.app.redirect_to_login();
					}
				}
			});
			dialog.set_primary_action(__('Login'), () => {
				dialog.set_message(__('Authenticating...'));
				capkpi.call({
					method: 'login',
					args: {
						usr: capkpi.session.user,
						pwd: dialog.get_values().password
					},
					callback: (r) => {
						if (r.message==='Logged In') {
							dialog.logged_in = true;

							// revert backdrop
							$('.modal-backdrop').css({
								'opacity': '',
								'background-color': '#334143'
							});
						}
						dialog.hide();
					},
					statusCode: () => {
						dialog.hide();
					}
				});
			});
			capkpi.app.session_expired_dialog = dialog;
		}
		if(!capkpi.app.session_expired_dialog.display) {
			capkpi.app.session_expired_dialog.show();
			// add backdrop
			$('.modal-backdrop').css({
				'opacity': 1,
				'background-color': '#4B4C9D'
			});
		}
	},
	redirect_to_login: function() {
		window.location.href = '/';
	},
	set_favicon: function() {
		var link = $('link[type="image/x-icon"]').remove().attr("href");
		$('<link rel="shortcut icon" href="' + link + '" type="image/x-icon">').appendTo("head");
		$('<link rel="icon" href="' + link + '" type="image/x-icon">').appendTo("head");
	},
	trigger_primary_action: function() {
		// to trigger change event on active input before triggering primary action
		$(document.activeElement).blur();
		// wait for possible JS validations triggered after blur (it might change primary button)
		setTimeout(() => {
			if (window.cur_dialog && cur_dialog.display) {
				// trigger primary
				cur_dialog.get_primary_btn().trigger("click");
			} else if (cur_frm && cur_frm.page.btn_primary.is(':visible')) {
				cur_frm.page.btn_primary.trigger('click');
			} else if (capkpi.container.page.save_action) {
				capkpi.container.page.save_action();
			}
		}, 100);
	},

	show_change_log: function() {
		var me = this;
		let change_log = capkpi.boot.change_log;

		// capkpi.boot.change_log = [{
		// 	"change_log": [
		// 		[<version>, <change_log in markdown>],
		// 		[<version>, <change_log in markdown>],
		// 	],
		// 	"description": "ERP made simple",
		// 	"title": "ERP",
		// 	"version": "12.2.0"
		// }];

		if (!Array.isArray(change_log) || !change_log.length ||
			window.Cypress || cint(capkpi.boot.sysdefaults.disable_change_log_notification)) {
			return;
		}

		// Iterate over changelog
		var change_log_dialog = capkpi.msgprint({
			message: capkpi.render_template("change_log", {"change_log": change_log}),
			title: __("Updated To A New Version 🎉"),
			wide: true,
		});
		change_log_dialog.keep_open = true;
		change_log_dialog.custom_onhide = function() {
			capkpi.call({
				"method": "capkpi.utils.change_log.update_last_known_versions"
			});
			me.show_notes();
		};
	},

	show_update_available: () => {
		if (capkpi.boot.sysdefaults.disable_system_update_notification) return;

		capkpi.call({
			"method": "capkpi.utils.change_log.show_update_popup"
		});
	},

	setup_analytics: function() {
		if(window.mixpanel) {
			window.mixpanel.identify(capkpi.session.user);
			window.mixpanel.people.set({
				"$first_name": capkpi.boot.user.first_name,
				"$last_name": capkpi.boot.user.last_name,
				"$created": capkpi.boot.user.creation,
				"$email": capkpi.session.user
			});
		}
	},

	add_browser_class() {
		$('html').addClass(capkpi.utils.get_browser().name.toLowerCase());
	},

	set_fullwidth_if_enabled() {
		capkpi.ui.toolbar.set_fullwidth_if_enabled();
	},

	show_notes: function() {
		var me = this;
		if(capkpi.boot.notes.length) {
			capkpi.boot.notes.forEach(function(note) {
				if(!note.seen || note.notify_on_every_login) {
					var d = capkpi.msgprint({message:note.content, title:note.title});
					d.keep_open = true;
					d.custom_onhide = function() {
						note.seen = true;

						// Mark note as read if the Notify On Every Login flag is not set
						if (!note.notify_on_every_login) {
							capkpi.call({
								method: "capkpi.desk.doctype.note.note.mark_as_seen",
								args: {
									note: note.name
								}
							});
						}

						// next note
						me.show_notes();

					};
				}
			});
		}
	},

	setup_build_error_listener() {
		if (capkpi.boot.developer_mode) {
			capkpi.realtime.on('build_error', (data) => {
				console.log(data);
			});
		}
	},

	setup_energy_point_listeners() {
		capkpi.realtime.on('energy_point_alert', (message) => {
			capkpi.show_alert(message);
		});
	},

	setup_copy_doc_listener() {
		$('body').on('paste', (e) => {
			try {
				let pasted_data = capkpi.utils.get_clipboard_data(e);
				let doc = JSON.parse(pasted_data);
				if (doc.doctype) {
					e.preventDefault();
					let sleep = (time) => {
						return new Promise((resolve) => setTimeout(resolve, time));
					};

					capkpi.dom.freeze(__('Creating {0}', [doc.doctype]) + '...');
					// to avoid abrupt UX
					// wait for activity feedback
					sleep(500).then(() => {
						let res = capkpi.model.with_doctype(doc.doctype, () => {
							let newdoc = capkpi.model.copy_doc(doc);
							newdoc.__newname = doc.name;
							delete doc.name;
							newdoc.idx = null;
							newdoc.__run_link_triggers = false;
							capkpi.set_route('Form', newdoc.doctype, newdoc.name);
							capkpi.dom.unfreeze();
						});
						res && res.fail(capkpi.dom.unfreeze);
					});
				}
			} catch (e) {
				//
			}
		});
	},

	setup_moment() {
		moment.updateLocale('en', {
			week: {
				dow: capkpi.datetime.get_first_day_of_the_week_index(),
			}
		});
		moment.locale("en");
		moment.user_utc_offset = moment().utcOffset();
		if (capkpi.boot.timezone_info) {
			moment.tz.add(capkpi.boot.timezone_info);
		}
	}
});

capkpi.get_module = function(m, default_module) {
	var module = capkpi.modules[m] || default_module;
	if (!module) {
		return;
	}

	if(module._setup) {
		return module;
	}

	if(!module.label) {
		module.label = m;
	}

	if(!module._label) {
		module._label = __(module.label);
	}

	module._setup = true;

	return module;
};
