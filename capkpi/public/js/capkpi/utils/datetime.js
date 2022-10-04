// Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

capkpi.provide('capkpi.datetime');

capkpi.defaultDateFormat = "YYYY-MM-DD";
capkpi.defaultTimeFormat = "HH:mm:ss";
capkpi.defaultDatetimeFormat = capkpi.defaultDateFormat + " " + capkpi.defaultTimeFormat;
moment.defaultFormat = capkpi.defaultDateFormat;

capkpi.provide("capkpi.datetime");

$.extend(capkpi.datetime, {
	convert_to_user_tz: function(date, format) {
		// format defaults to true
		if(capkpi.sys_defaults.time_zone) {
			var date_obj = moment.tz(date, capkpi.sys_defaults.time_zone).local();
		} else {
			var date_obj = moment(date);
		}

		return (format===false) ? date_obj : date_obj.format(capkpi.defaultDatetimeFormat);
	},

	convert_to_system_tz: function(date, format) {
		// format defaults to true

		if(capkpi.sys_defaults.time_zone) {
			var date_obj = moment(date).tz(capkpi.sys_defaults.time_zone);
		} else {
			var date_obj = moment(date);
		}

		return (format===false) ? date_obj : date_obj.format(capkpi.defaultDatetimeFormat);
	},

	is_timezone_same: function() {
		if(capkpi.sys_defaults.time_zone) {
			return moment().tz(capkpi.sys_defaults.time_zone).utcOffset() === moment().utcOffset();
		} else {
			return true;
		}
	},

	str_to_obj: function(d) {
		return moment(d, capkpi.defaultDatetimeFormat)._d;
	},

	obj_to_str: function(d) {
		return moment(d).locale("en").format();
	},

	obj_to_user: function(d) {
		return moment(d).format(capkpi.datetime.get_user_date_fmt().toUpperCase());
	},

	get_diff: function(d1, d2) {
		return moment(d1).diff(d2, "days");
	},

	get_hour_diff: function(d1, d2) {
		return moment(d1).diff(d2, "hours");
	},

	get_day_diff: function(d1, d2) {
		return moment(d1).diff(d2, "days");
	},

	add_days: function(d, days) {
		return moment(d).add(days, "days").format();
	},

	add_months: function(d, months) {
		return moment(d).add(months, "months").format();
	},

	week_start: function() {
		return moment().startOf("week").format();
	},

	week_end: function() {
		return moment().endOf("week").format();
	},

	month_start: function() {
		return moment().startOf("month").format();
	},

	month_end: function() {
		return moment().endOf("month").format();
	},

	quarter_start: function() {
		return moment().startOf("quarter").format();
	},

	quarter_end: function() {
		return moment().endOf("quarter").format();
	},

	year_start: function(){
		return moment().startOf("year").format();
	},

	year_end: function(){
		return moment().endOf("year").format();
	},

	get_user_time_fmt: function() {
		return capkpi.sys_defaults && capkpi.sys_defaults.time_format || "HH:mm:ss";
	},

	get_user_date_fmt: function() {
		return capkpi.sys_defaults && capkpi.sys_defaults.date_format || "yyyy-mm-dd";
	},

	get_user_fmt: function() {  // For backwards compatibility only
		return capkpi.sys_defaults && capkpi.sys_defaults.date_format || "yyyy-mm-dd";
	},

	str_to_user: function(val, only_time = false) {
		if(!val) return "";

		var user_time_fmt = capkpi.datetime.get_user_time_fmt();
		if(only_time) {
			return moment(val, capkpi.defaultTimeFormat)
				.format(user_time_fmt);
		}

		var user_date_fmt = capkpi.datetime.get_user_date_fmt().toUpperCase();
		if(typeof val !== "string" || val.indexOf(" ")===-1) {
			return moment(val).format(user_date_fmt);
		} else {
			return moment(val, "YYYY-MM-DD HH:mm:ss").format(user_date_fmt + " " + user_time_fmt);
		}
	},

	get_datetime_as_string: function(d) {
		return moment(d).format("YYYY-MM-DD HH:mm:ss");
	},

	user_to_str: function(val, only_time = false) {

		var user_time_fmt = capkpi.datetime.get_user_time_fmt();
		if(only_time) {
			return moment(val, user_time_fmt)
				.format(capkpi.defaultTimeFormat);
		}

		var user_fmt = capkpi.datetime.get_user_date_fmt().toUpperCase();
		var system_fmt = "YYYY-MM-DD";

		if(val.indexOf(" ")!==-1) {
			user_fmt += " " + user_time_fmt;
			system_fmt += " HH:mm:ss";
		}

		// user_fmt.replace("YYYY", "YY")? user might only input 2 digits of the year, which should also be parsed
		return moment(val, [user_fmt.replace("YYYY", "YY"),
			user_fmt]).locale("en").format(system_fmt);
	},

	user_to_obj: function(d) {
		return capkpi.datetime.str_to_obj(capkpi.datetime.user_to_str(d));
	},

	global_date_format: function(d) {
		var m = moment(d);
		if(m._f && m._f.indexOf("HH")!== -1) {
			return m.format("Do MMMM YYYY, h:mma")
		} else {
			return m.format('Do MMMM YYYY');
		}
	},

	now_date: function(as_obj = false) {
		return capkpi.datetime._date(capkpi.defaultDateFormat, as_obj);
	},

	now_time: function(as_obj = false) {
		return capkpi.datetime._date(capkpi.defaultTimeFormat, as_obj);
	},

	now_datetime: function(as_obj = false) {
		return capkpi.datetime._date(capkpi.defaultDatetimeFormat, as_obj);
	},

	_date: function(format, as_obj = false) {
		const time_zone = capkpi.sys_defaults && capkpi.sys_defaults.time_zone;
		let date;
		if (time_zone) {
			date = moment.tz(time_zone);
		} else {
			date = moment();
		}
		if (as_obj) {
			return capkpi.datetime.moment_to_date_obj(date);
		} else {
			return date.format(format);
		}
	},

	moment_to_date_obj: function(moment) {
		const date_obj = new Date();
		const date_array = moment.toArray();
		date_obj.setFullYear(date_array[0]);
		date_obj.setMonth(date_array[1]);
		date_obj.setDate(date_array[2]);
		date_obj.setHours(date_array[3]);
		date_obj.setMinutes(date_array[4]);
		date_obj.setSeconds(date_array[5]);
		date_obj.setMilliseconds(date_array[6]);
		return date_obj;
	},

	nowdate: function() {
		return capkpi.datetime.now_date();
	},

	get_today: function() {
		return capkpi.datetime.now_date();
	},

	get_time: (timestamp) => {
		// return time with AM/PM
		return moment(timestamp).format('hh:mm A');
	},

	validate: function(d) {
		return moment(d, [
			capkpi.defaultDateFormat,
			capkpi.defaultDatetimeFormat,
			capkpi.defaultTimeFormat
		], true).isValid();
	},

	get_first_day_of_the_week_index() {
		const first_day_of_the_week = capkpi.sys_defaults.first_day_of_the_week || "Sunday";
		return moment.weekdays().indexOf(first_day_of_the_week);
	}

});

// Proxy for dateutil and get_today
Object.defineProperties(window, {
	'dateutil': {
		get: function() {
			console.warn('Please use `capkpi.datetime` instead of `dateutil`. It will be deprecated soon.');
			return capkpi.datetime;
		},
		configurable: true
	},
	'date': {
		get: function() {
			console.warn('Please use `capkpi.datetime` instead of `date`. It will be deprecated soon.');
			return capkpi.datetime;
		},
		configurable: true
	},
	'get_today': {
		get: function() {
			console.warn('Please use `capkpi.datetime.get_today` instead of `get_today`. It will be deprecated soon.');
			return capkpi.datetime.get_today;
		},
		configurable: true
	}
});
