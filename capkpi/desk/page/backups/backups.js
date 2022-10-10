capkpi.pages['backups'].on_page_load = function(wrapper) {
	var page = capkpi.ui.make_app_page({
		parent: wrapper,
		title: __('Download Backups'),
		single_column: true
	});

	page.add_inner_button(__("Set Number of Backups"), function () {
		capkpi.set_route('Form', 'System Settings');
	});

	page.add_inner_button(__("Download Files Backup"), function () {
		capkpi.call({
			method:"capkpi.desk.page.backups.backups.schedule_files_backup",
			args: {"user_email": capkpi.session.user_email}
		});
	});

	capkpi.breadcrumbs.add("Setup");

	$(capkpi.render_template("backups")).appendTo(page.body.addClass("no-border"));
}
