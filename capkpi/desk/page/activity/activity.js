// Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
// License: See license.txt

capkpi.provide("capkpi.activity");

capkpi.pages['activity'].on_page_load = function (wrapper) {
	var me = this;

	capkpi.ui.make_app_page({
		parent: wrapper,
		single_column: true
	});

	me.page = wrapper.page;
	me.page.set_title(__("Activity"));

	capkpi.model.with_doctype("Communication", function () {
		me.page.list = new capkpi.views.Activity({
			doctype: 'Communication',
			parent: wrapper
		});
	});

	capkpi.activity.render_heatmap(me.page);

	me.page.main.on("click", ".activity-message", function () {
		var link_doctype = $(this).attr("data-link-doctype"),
			link_name = $(this).attr("data-link-name"),
			doctype = $(this).attr("data-doctype"),
			docname = $(this).attr("data-docname");

		[link_doctype, link_name, doctype, docname] =
			[link_doctype, link_name, doctype, docname].map(decodeURIComponent);

		link_doctype = link_doctype && link_doctype !== 'null' ? link_doctype : null;
		link_name = link_name && link_name !== 'null' ? link_name : null;

		if (doctype && docname) {
			if (link_doctype && link_name) {
				capkpi.route_options = {
					scroll_to: { "doctype": doctype, "name": docname }
				}
			}

			capkpi.set_route(["Form", link_doctype || doctype, link_name || docname]);
		}
	});

	// Build Report Button
	if (capkpi.boot.user.can_get_report.indexOf("Feed") != -1) {
		this.page.add_menu_item(__('Build Report'), function () {
			capkpi.set_route("List", "Feed", "Report");
		}, 'fa fa-th')
	}

	this.page.add_menu_item(__('Activity Log'), function () {
		capkpi.route_options = {
			"user": capkpi.session.user
		}

		capkpi.set_route("List", "Activity Log", "Report");
	}, 'fa fa-th');
};

capkpi.pages['activity'].on_page_show = function () {
	capkpi.breadcrumbs.add("Desk");
}

capkpi.activity.last_feed_date = false;
capkpi.activity.Feed = Class.extend({
	init: function (row, data) {
		this.scrub_data(data);
		this.add_date_separator(row, data);
		if (!data.add_class)
			data.add_class = "label-default";

		data.link = "";
		if (data.link_doctype && data.link_name) {
			data.link = capkpi.format(data.link_name, { fieldtype: "Link", options: data.link_doctype },
				{ label: __(data.link_doctype) + " " + __(data.link_name) });

		} else if (data.feed_type === "Comment" && data.comment_type === "Comment") {
			// hack for backward compatiblity
			data.link_doctype = data.reference_doctype;
			data.link_name = data.reference_name;
			data.reference_doctype = "Communication";
			data.reference_name = data.name;

			data.link = capkpi.format(data.link_name, { fieldtype: "Link", options: data.link_doctype },
				{ label: __(data.link_doctype) + " " + __(data.link_name) });

		} else if (data.reference_doctype && data.reference_name) {
			data.link = capkpi.format(data.reference_name, { fieldtype: "Link", options: data.reference_doctype },
				{ label: __(data.reference_doctype) + " " + __(data.reference_name) });
		}

		$(row)
			.append(capkpi.render_template("activity_row", data))
			.find("a").addClass("grey");
	},
	scrub_data: function (data) {
		data.by = capkpi.user.full_name(data.owner);
		data.avatar = capkpi.avatar(data.owner);

		data.icon = "fa fa-flag";

		// color for comment
		data.add_class = {
			"Comment": "label-danger",
			"Assignment": "label-warning",
			"Login": "label-default"
		}[data.comment_type || data.communication_medium] || "label-info"

		data.when = comment_when(data.creation);
		data.feed_type = data.comment_type || data.communication_medium;
	},

	add_date_separator: function (row, data) {
		var date = capkpi.datetime.str_to_obj(data.creation);
		var last = capkpi.activity.last_feed_date;

		if ((last && capkpi.datetime.obj_to_str(last) != capkpi.datetime.obj_to_str(date)) || (!last)) {
			var diff = capkpi.datetime.get_day_diff(capkpi.datetime.get_today(), capkpi.datetime.obj_to_str(date));
			var pdate;
			if (diff < 1) {
				pdate = 'Today';
			} else if (diff < 2) {
				pdate = 'Yesterday';
			} else {
				pdate = capkpi.datetime.global_date_format(date);
			}
			data.date_sep = pdate;
			data.date_class = pdate == 'Today' ? "date-indicator blue" : "date-indicator";
		} else {
			data.date_sep = null;
			data.date_class = "";
		}
		capkpi.activity.last_feed_date = date;
	}
});

capkpi.activity.render_heatmap = function (page) {
	$('<div class="heatmap-container" style="text-align:center">\
		<div class="heatmap" style="display:inline-block;"></div></div>\
		<hr style="margin-bottom: 0px;">').prependTo(page.main);

	capkpi.call({
		method: "capkpi.desk.page.activity.activity.get_heatmap_data",
		callback: function (r) {
			if (r.message) {
				new capkpi.Chart(".heatmap", {
					type: 'heatmap',
					start: new Date(moment().subtract(1, 'year').toDate()),
					countLabel: "actions",
					discreteDomains: 1,
					radius: 3, // default 0
					data: {
						'dataPoints': r.message
					}
				});
			}
		}
	});
};

capkpi.views.Activity = class Activity extends capkpi.views.BaseList {
	constructor(opts) {
		super(opts);
		this.show();
	}

	setup_defaults() {
		super.setup_defaults();

		this.page_title = __('Activity');
		this.doctype = 'Communication';
		this.method = 'capkpi.desk.page.activity.activity.get_feed';

	}

	setup_filter_area() {
		//
	}

	setup_view_menu() {
		//
	}

	setup_sort_selector() {

	}

	setup_side_bar() {

	}

	get_args() {
		return {
			start: this.start,
			page_length: this.page_length
		};
	}

	update_data(r) {
		let data = r.message || [];

		if (this.start === 0) {
			this.data = data;
		} else {
			this.data = this.data.concat(data);
		}
	}

	render() {
		this.data.map(value => {
			const row = $('<div class="list-row">').data("data", value).appendTo(this.$result).get(0);
			new capkpi.activity.Feed(row, value);
		});
	}
};
