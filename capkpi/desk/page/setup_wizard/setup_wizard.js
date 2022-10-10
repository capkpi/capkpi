capkpi.provide("capkpi.setup");
capkpi.provide("capkpi.setup.events");
capkpi.provide("capkpi.ui");

capkpi.setup = {
	slides: [],
	events: {},
	data: {},
	utils: {},
	domains: [],

	on: function (event, fn) {
		if (!capkpi.setup.events[event]) {
			capkpi.setup.events[event] = [];
		}
		capkpi.setup.events[event].push(fn);
	},
	add_slide: function (slide) {
		capkpi.setup.slides.push(slide);
	},

	remove_slide: function (slide_name) {
		capkpi.setup.slides = capkpi.setup.slides.filter((slide) => slide.name !== slide_name);
	},

	run_event: function (event) {
		$.each(capkpi.setup.events[event] || [], function (i, fn) {
			fn();
		});
	}
}

capkpi.pages['setup-wizard'].on_page_load = function (wrapper) {
	let requires = (capkpi.boot.setup_wizard_requires || []);
	capkpi.require(requires, function () {
		capkpi.call({
			method: "capkpi.desk.page.setup_wizard.setup_wizard.load_languages",
			freeze: true,
			callback: function (r) {
				capkpi.setup.data.lang = r.message;

				capkpi.setup.run_event("before_load");
				var wizard_settings = {
					parent: wrapper,
					slides: capkpi.setup.slides,
					slide_class: capkpi.setup.SetupWizardSlide,
					unidirectional: 1,
					done_state: 1,
				}
				capkpi.wizard = new capkpi.setup.SetupWizard(wizard_settings);
				capkpi.setup.run_event("after_load");
				// capkpi.wizard.values = test_values_edu;
				let route = capkpi.get_route();
				if (route) {
					capkpi.wizard.show_slide(route[1]);
				}
			}
		});
	});
};

capkpi.pages['setup-wizard'].on_page_show = function () {
	if (capkpi.get_route()[1]) {
		capkpi.wizard && capkpi.wizard.show_slide(capkpi.get_route()[1]);
	}
};

capkpi.setup.on("before_load", function () {
	// load slides
	capkpi.setup.slides_settings.forEach((s) => {
		if (!(s.name === 'user' && capkpi.boot.developer_mode)) {
			// if not user slide with developer mode
			capkpi.setup.add_slide(s);
		}
	});
});

capkpi.setup.SetupWizard = class SetupWizard extends capkpi.ui.Slides {
	constructor(args = {}) {
		super(args);
		$.extend(this, args);

		this.page_name = "setup-wizard";
		this.welcomed = true;
		capkpi.set_route("setup-wizard/0");
	}

	make() {
		super.make();
		this.container.addClass("container setup-wizard-slide with-form");
		this.$next_btn.addClass('action');
		this.$complete_btn.addClass('action');
		this.setup_keyboard_nav();
	}

	setup_keyboard_nav() {
		$('body').on('keydown', this.handle_enter_press.bind(this));
	}

	disable_keyboard_nav() {
		$('body').off('keydown', this.handle_enter_press.bind(this));
	}

	handle_enter_press(e) {
		if (e.which === capkpi.ui.keyCode.ENTER) {
			var $target = $(e.target);
			if ($target.hasClass('prev-btn')) {
				$target.trigger('click');
			} else {
				this.container.find('.next-btn').trigger('click');
				e.preventDefault();
			}
		}
	}

	before_show_slide() {
		if (!this.welcomed) {
			capkpi.set_route(this.page_name);
			return false;
		}
		return true;
	}

	show_slide(id) {
		if (id === this.slides.length) {
			// show_slide called on last slide
			this.action_on_complete();
			return;
		}
		super.show_slide(id);
		capkpi.set_route(this.page_name, id + "");
	}

	show_hide_prev_next(id) {
		super.show_hide_prev_next(id);
		if (id + 1 === this.slides.length) {
			this.$next_btn.removeClass("btn-primary").hide();
			this.$complete_btn.addClass("btn-primary").show()
				.on('click', () => this.action_on_complete());
		} else {
			this.$next_btn.addClass("btn-primary").show();
			this.$complete_btn.removeClass("btn-primary").hide();
		}
	}

	refresh_slides() {
		// For Translations, etc.
		if (this.in_refresh_slides || !this.current_slide.set_values()) {
			return;
		}
		this.in_refresh_slides = true;

		this.update_values();
		capkpi.setup.slides = [];
		capkpi.setup.run_event("before_load");

		capkpi.setup.slides = this.get_setup_slides_filtered_by_domain();

		this.slides = capkpi.setup.slides;
		capkpi.setup.run_event("after_load");

		// re-render all slide, only remake made slides
		$.each(this.slide_dict, (id, slide) => {
			if (slide.made) {
				this.made_slide_ids.push(id);
			}
		});
		this.made_slide_ids.push(this.current_id);
		this.setup();

		this.show_slide(this.current_id);
		this.refresh(this.current_id);
		setTimeout(() => {
			this.container.find('.form-control').first().focus();
		}, 200);
		this.in_refresh_slides = false;
	}

	action_on_complete() {
		if (!this.current_slide.set_values()) return;
		this.update_values();
		this.show_working_state();
		this.disable_keyboard_nav();
		this.listen_for_setup_stages();

		return capkpi.call({
			method: "capkpi.desk.page.setup_wizard.setup_wizard.setup_complete",
			args: { args: this.values },
			callback: (r) => {
				if (r.message.status === 'ok') {
					this.post_setup_success();
				} else if (r.message.fail !== undefined) {
					this.abort_setup(r.message.fail);
				}
			},
			error: () => this.abort_setup("Error in setup")
		});
	}

	post_setup_success() {
		this.set_setup_complete_message(__("Setup Complete"), __("Refreshing..."));
		if (capkpi.setup.welcome_page) {
			localStorage.setItem("session_last_route", capkpi.setup.welcome_page);
		}
		setTimeout(function () {
			// Reload
			window.location.href = '/app';
		}, 2000);
	}

	abort_setup(fail_msg) {
		this.$working_state.find('.state-icon-container').html('');
		fail_msg = fail_msg ? fail_msg : __("Failed to complete setup");

		this.update_setup_message('Could not start up: ' + fail_msg);

		this.$working_state.find('.title').html('Setup failed');

		this.$abort_btn.show();
	}

	listen_for_setup_stages() {
		capkpi.realtime.on("setup_task", (data) => {
			// console.log('data', data);
			if (data.stage_status) {
				// .html('Process '+ data.progress[0] + ' of ' + data.progress[1] + ': ' + data.stage_status);
				this.update_setup_message(data.stage_status);
				this.set_setup_load_percent((data.progress[0] + 1) / data.progress[1] * 100);
			}
			if (data.fail_msg) {
				this.abort_setup(data.fail_msg);
			}
		})
	}

	update_setup_message(message) {
		this.$working_state.find('.setup-message').html(message);
	}

	get_setup_slides_filtered_by_domain() {
		var filtered_slides = [];
		capkpi.setup.slides.forEach(function (slide) {
			if (capkpi.setup.domains) {
				let active_domains = capkpi.setup.domains;
				if (!slide.domains ||
					slide.domains.filter(d => active_domains.includes(d)).length > 0) {
					filtered_slides.push(slide);
				}
			} else {
				filtered_slides.push(slide);
			}
		})
		return filtered_slides;
	}

	show_working_state() {
		this.container.hide();
		capkpi.set_route(this.page_name);

		this.$working_state = this.get_message(
			__("Setting up your system"),
			__("Starting CapKPI ...")).appendTo(this.parent);

		this.attach_abort_button();

		this.current_id = this.slides.length;
		this.current_slide = null;
	}

	attach_abort_button() {
		this.$abort_btn = $(`<button class='btn btn-secondary btn-xs btn-abort text-muted'>${__('Retry')}</button>`);
		this.$working_state.find('.content').append(this.$abort_btn);

		this.$abort_btn.on('click', () => {
			$(this.parent).find('.setup-in-progress').remove();
			this.container.show();
			capkpi.set_route(this.page_name, this.slides.length - 1);
		});

		this.$abort_btn.hide();
	}

	get_message(title, message = "") {
		const loading_html = `<div class="progress-chart">
			<div class="progress">
				<div class="progress-bar"></div>
			</div>
		</div>`;

		return $(`<div class="slides-wrapper container setup-wizard-slide setup-in-progress">
			<div class="content text-center">
				<h1 class="slide-title title">${title}</h1>
				<div class="state-icon-container">${loading_html}</div>
				<p class="setup-message text-muted">${message}</p>
			</div>
		</div>`);
	}

	set_setup_complete_message(title, message) {
		this.$working_state.find('.title').html(title);
		this.$working_state.find('.setup-message').html(message);
	}

	set_setup_load_percent(percent) {
		this.$working_state.find('.progress-bar').css({ "width": percent + "%" });
	}
};

capkpi.setup.SetupWizardSlide = class SetupWizardSlide extends capkpi.ui.Slide {
	constructor(slide = null) {
		super(slide);
	}

	make() {
		super.make();
		this.set_init_values();
		this.reset_action_button_state();
	}

	set_init_values() {
		var me = this;
		// set values from capkpi.setup.values
		if (capkpi.wizard.values && this.fields) {
			this.fields.forEach(function (f) {
				var value = capkpi.wizard.values[f.fieldname];
				if (value) {
					me.get_field(f.fieldname).set_input(value);
				}
			});
		}
	}

};

// CapKPI slides settings
// ======================================================
capkpi.setup.slides_settings = [
	{
		// Welcome (language) slide
		name: "welcome",
		title: __("Hello!"),
		icon: "fa fa-world",
		// help: __("Let's prepare the system for first use."),

		fields: [
			{
				fieldname: "language", label: __("Your Language"),
				fieldtype: "Select", reqd: 1
			}
		],

		onload: function (slide) {
			this.setup_fields(slide);
			let browser_language = capkpi.setup.utils.get_language_name_from_code(navigator.language);
			let language_field = slide.get_field("language");

			language_field.set_input(browser_language || "English");

			if (!capkpi.setup._from_load_messages) {
				language_field.$input.trigger("change");
			}
			delete capkpi.setup._from_load_messages;
			moment.locale("en");
		},

		setup_fields: function (slide) {
			capkpi.setup.utils.setup_language_field(slide);
			capkpi.setup.utils.bind_language_events(slide);
		},
	},

	{
		// Region slide
		name: 'region',
		title: __("Select Your Region"),
		icon: "fa fa-flag",
		// help: __("Select your Country, Time Zone and Currency"),
		fields: [
			{
				fieldname: "country", label: __("Your Country"), reqd: 1,
				fieldtype: "Autocomplete",
				placeholder: __('Select Country')
			},
			{ fieldtype: "Section Break" },
			{
				fieldname: "timezone",
				label: __("Time Zone"),
				placeholder: __('Select Time Zone'),
				reqd: 1,
				fieldtype: "Select",
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "currency",
				label: __("Currency"),
				placeholder: __('Select Currency'),
				reqd: 1,
				fieldtype: "Select",
			}
		],

		onload: function (slide) {
			if (capkpi.setup.data.regional_data) {
				this.setup_fields(slide);
			} else {
				capkpi.setup.utils.load_regional_data(slide, this.setup_fields);
			}
		},

		setup_fields: function (slide) {
			capkpi.setup.utils.setup_region_fields(slide);
			capkpi.setup.utils.bind_region_events(slide);
		}
	},

	{
		// Profile slide
		name: 'user',
		title: __("The First User: You"),
		icon: "fa fa-user",
		fields: [
			{
				"fieldtype": "Attach Image", "fieldname": "attach_user_image",
				label: __("Attach Your Picture"), is_private: 0, align: 'center'
			},
			{
				"fieldname": "full_name", "label": __("Full Name"), "fieldtype": "Data",
				reqd: 1
			},
			{
				"fieldname": "email", "label": __("Email Address") + ' (' + __("Will be your login ID") + ')',
				"fieldtype": "Data", "options": "Email"
			},
			{ "fieldname": "password", "label": __("Password"), "fieldtype": "Password" }
		],
		// help: __('The first user will become the System Manager (you can change this later).'),
		onload: function (slide) {
			if (capkpi.session.user !== "Administrator") {
				slide.form.fields_dict.email.$wrapper.toggle(false);
				slide.form.fields_dict.password.$wrapper.toggle(false);

				// remove password field
				delete slide.form.fields_dict.password;

				if (capkpi.boot.user.first_name || capkpi.boot.user.last_name) {
					slide.form.fields_dict.full_name.set_input(
						[capkpi.boot.user.first_name, capkpi.boot.user.last_name].join(' ').trim());
				}

				var user_image = capkpi.get_cookie("user_image");
				var $attach_user_image = slide.form.fields_dict.attach_user_image.$wrapper;

				if (user_image) {
					$attach_user_image.find(".missing-image").toggle(false);
					$attach_user_image.find("img").attr("src", decodeURIComponent(user_image));
					$attach_user_image.find(".img-container").toggle(true);
				}
				delete slide.form.fields_dict.email;

			} else {
				slide.form.fields_dict.email.df.reqd = 1;
				slide.form.fields_dict.email.refresh();
				slide.form.fields_dict.password.df.reqd = 1;
				slide.form.fields_dict.password.refresh();

				capkpi.setup.utils.load_user_details(slide, this.setup_fields);
			}
		},

		setup_fields: function (slide) {
			if (capkpi.setup.data.full_name) {
				slide.form.fields_dict.full_name.set_input(capkpi.setup.data.full_name);
			}
			if (capkpi.setup.data.email) {
				let email = capkpi.setup.data.email;
				slide.form.fields_dict.email.set_input(email);
				if (capkpi.get_gravatar(email, 200)) {
					var $attach_user_image = slide.form.fields_dict.attach_user_image.$wrapper;
					$attach_user_image.find(".missing-image").toggle(false);
					$attach_user_image.find("img").attr("src", capkpi.get_gravatar(email, 200));
					$attach_user_image.find(".img-container").toggle(true);
				}
			}
		},
	}
];

capkpi.setup.utils = {
	load_regional_data: function (slide, callback) {
		capkpi.call({
			method: "capkpi.geo.country_info.get_country_timezone_info",
			callback: function (data) {
				capkpi.setup.data.regional_data = data.message;
				callback(slide);
			}
		});
	},

	load_user_details: function (slide, callback) {
		capkpi.call({
			method: "capkpi.desk.page.setup_wizard.setup_wizard.load_user_details",
			freeze: true,
			callback: function (r) {
				capkpi.setup.data.full_name = r.message.full_name;
				capkpi.setup.data.email = r.message.email;
				callback(slide);
			}
		});
	},

	setup_language_field: function (slide) {
		var language_field = slide.get_field("language");
		language_field.df.options = capkpi.setup.data.lang.languages;
		language_field.refresh();
	},

	setup_region_fields: function (slide) {
		/*
			Set a slide's country, timezone and currency fields
		*/
		let data = capkpi.setup.data.regional_data;
		let country_field = slide.get_field('country');
		let translated_countries = [];

		Object.keys(data.country_info).sort().forEach(country => {
			translated_countries.push({
				label: __(country),
				value: country
			});
		});

		country_field.set_data(translated_countries);

		slide.get_input("currency")
			.empty()
			.add_options(
				capkpi.utils.unique(
					$.map(data.country_info, opts => opts.currency).sort()
				)
			);

		slide.get_input("timezone").empty()
			.add_options(data.all_timezones);

		// set values if present
		if (capkpi.wizard.values.country) {
			country_field.set_input(capkpi.wizard.values.country);
		} else if (data.default_country) {
			country_field.set_input(data.default_country);
		}

		slide.get_field("currency").set_input(capkpi.wizard.values.currency);

		slide.get_field("timezone").set_input(capkpi.wizard.values.timezone);

	},

	bind_language_events: function (slide) {
		slide.get_input("language").unbind("change").on("change", function () {
			clearTimeout(slide.language_call_timeout);
			slide.language_call_timeout = setTimeout(() => {
				var lang = $(this).val() || "English";
				capkpi._messages = {};
				capkpi.call({
					method: "capkpi.desk.page.setup_wizard.setup_wizard.load_messages",
					freeze: true,
					args: {
						language: lang
					},
					callback: function () {
						capkpi.setup._from_load_messages = true;
						capkpi.wizard.refresh_slides();
					}
				});
			}, 500);
		});
	},

	get_language_name_from_code: function (language_code) {
		return capkpi.setup.data.lang.codes_to_names[language_code] || "English";
	},

	bind_region_events: function (slide) {
		/*
			Bind a slide's country, timezone and currency fields
		*/
		slide.get_input("country").on("change", function () {
			var country = slide.get_input("country").val();
			var $timezone = slide.get_input("timezone");
			var data = capkpi.setup.data.regional_data;

			$timezone.empty();

			if (!country) return;
			// add country specific timezones first
			const timezone_list = data.country_info[country].timezones || [];
			$timezone.add_options(timezone_list.sort());
			slide.get_field("currency").set_input(data.country_info[country].currency);
			slide.get_field("currency").$input.trigger("change");

			// add all timezones at the end, so that user has the option to change it to any timezone
			$timezone.add_options(data.all_timezones);
			slide.get_field("timezone").set_input($timezone.val());

			// temporarily set date format
			capkpi.boot.sysdefaults.date_format = (data.country_info[country].date_format
				|| "dd-mm-yyyy");
		});

		slide.get_input("currency").on("change", function () {
			var currency = slide.get_input("currency").val();
			if (!currency) return;
			capkpi.model.with_doc("Currency", currency, function () {
				capkpi.provide("locals.:Currency." + currency);
				var currency_doc = capkpi.model.get_doc("Currency", currency);
				var number_format = currency_doc.number_format;
				if (number_format === "#.###") {
					number_format = "#.###,##";
				} else if (number_format === "#,###") {
					number_format = "#,###.##";
				}

				capkpi.boot.sysdefaults.number_format = number_format;
				locals[":Currency"][currency] = $.extend({}, currency_doc);
			});
		});
	},
};
