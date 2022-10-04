# Copyright (c) 2020, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi


def execute():
	"""Set default module for standard Web Template, if none."""
	capkpi.reload_doc("website", "doctype", "Web Template Field")
	capkpi.reload_doc("website", "doctype", "web_template")

	standard_templates = capkpi.get_list("Web Template", {"standard": 1})
	for template in standard_templates:
		doc = capkpi.get_doc("Web Template", template.name)
		if not doc.module:
			doc.module = "Website"
			doc.save()
