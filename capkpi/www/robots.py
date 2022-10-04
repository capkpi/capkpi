from __future__ import unicode_literals

import capkpi

base_template_path = "templates/www/robots.txt"


def get_context(context):
	robots_txt = (
		capkpi.db.get_single_value("Website Settings", "robots_txt")
		or (capkpi.local.conf.robots_txt and capkpi.read_file(capkpi.local.conf.robots_txt))
		or ""
	)

	return {"robots_txt": robots_txt}
