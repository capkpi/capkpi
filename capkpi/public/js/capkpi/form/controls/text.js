capkpi.ui.form.ControlText = capkpi.ui.form.ControlData.extend({
	html_element: "textarea",
	horizontal: false,
	make_wrapper: function() {
		this._super();
		this.$wrapper.find(".like-disabled-input").addClass("for-description");
	},
	make_input: function() {
		this._super();
		this.$input.css({'height': '300px'});
	}
});

capkpi.ui.form.ControlLongText = capkpi.ui.form.ControlText;
capkpi.ui.form.ControlSmallText = capkpi.ui.form.ControlText.extend({
	make_input: function() {
		this._super();
		this.$input.css({'height': '150px'});
	}
});
