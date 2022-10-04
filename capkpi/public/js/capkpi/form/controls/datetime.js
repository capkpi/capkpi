capkpi.ui.form.ControlDatetime = capkpi.ui.form.ControlDate.extend({
	set_date_options: function() {
		this._super();
		this.today_text = __("Now");
		let sysdefaults = capkpi.boot.sysdefaults;
		this.date_format = capkpi.defaultDatetimeFormat;
		let time_format = sysdefaults && sysdefaults.time_format
			? sysdefaults.time_format : 'HH:mm:ss';
		$.extend(this.datepicker_options, {
			timepicker: true,
			timeFormat: time_format.toLowerCase().replace("mm", "ii")
		});
	},
	get_now_date: function() {
		return capkpi.datetime.now_datetime(true);
	},
	set_description: function() {
		const { description } = this.df;
		const { time_zone } = capkpi.sys_defaults;
		if (!this.df.hide_timezone && !capkpi.datetime.is_timezone_same()) {
			if (!description) {
				this.df.description = time_zone;
			} else if (!description.includes(time_zone)) {
				this.df.description += '<br>' + time_zone;
			}
		}
		this._super();
	},
	set_datepicker: function() {
		this._super();
		if (this.datepicker.opts.timeFormat.indexOf('s') == -1) {
			// No seconds in time format
			const $tp = this.datepicker.timepicker;
			$tp.$seconds.parent().css('display', 'none');
			$tp.$secondsText.css('display', 'none');
			$tp.$secondsText.prev().css('display', 'none');
		}
	},
	get_model_value() {
		let value = this._super();
		return !value ? "" : capkpi.datetime.get_datetime_as_string(value);
	}
});
