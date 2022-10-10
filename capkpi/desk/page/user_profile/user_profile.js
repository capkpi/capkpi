capkpi.pages['user-profile'].on_page_load = function (wrapper) {
	capkpi.require('assets/js/user_profile_controller.min.js', () => {
		let user_profile = new capkpi.ui.UserProfile(wrapper);
		user_profile.show();
	});
};