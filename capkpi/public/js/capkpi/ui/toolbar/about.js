capkpi.provide('capkpi.ui.misc');
capkpi.ui.misc.about = function() {
	if(!capkpi.ui.misc.about_dialog) {
		var d = new capkpi.ui.Dialog({title: __('CapKPI Framework')});

		$(d.body).html(repl("<div>\
		<p>"+__("Open Source Applications for the Web")+"</p>  \
		<p><i class='fa fa-globe fa-fw'></i>\
			Website: <a href='https://capkpiframework.com' target='_blank'>https://capkpiframework.com</a></p>\
		<p><i class='fa fa-github fa-fw'></i>\
			Source: <a href='https://github.com/capkpi' target='_blank'>https://github.com/capkpi</a></p>\
		<p><i class='fa fa-linkedin fa-fw'></i>\
			Linkedin: <a href='https://linkedin.com/company/capkpi-tech' target='_blank'>https://linkedin.com/company/capkpi-tech</a></p>\
		<p><i class='fa fa-facebook fa-fw'></i>\
			Facebook: <a href='https://facebook.com/erp' target='_blank'>https://facebook.com/erp</a></p>\
		<p><i class='fa fa-twitter fa-fw'></i>\
			Twitter: <a href='https://twitter.com/erp' target='_blank'>https://twitter.com/erp</a></p>\
		<hr>\
		<h4>Installed Apps</h4>\
		<div id='about-app-versions'>Loading versions...</div>\
		<hr>\
		<p class='text-muted'>&copy; CapKPI Technologies Pvt. Ltd and contributors </p> \
		</div>", capkpi.app));

		capkpi.ui.misc.about_dialog = d;

		capkpi.ui.misc.about_dialog.on_page_show = function() {
			if(!capkpi.versions) {
				capkpi.call({
					method: "capkpi.utils.change_log.get_versions",
					callback: function(r) {
						show_versions(r.message);
					}
				})
			} else {
				show_versions(capkpi.versions);
			}
		};

		var show_versions = function(versions) {
			var $wrap = $("#about-app-versions").empty();
			$.each(Object.keys(versions).sort(), function(i, key) {
				var v = versions[key];
				if(v.branch) {
					var text = $.format('<p><b>{0}:</b> v{1} ({2})<br></p>',
						[v.title, v.branch_version || v.version, v.branch])
				} else {
					var text = $.format('<p><b>{0}:</b> v{1}<br></p>',
						[v.title, v.version])
				}
				$(text).appendTo($wrap);
			});

			capkpi.versions = versions;
		}

	}

	capkpi.ui.misc.about_dialog.show();

}
