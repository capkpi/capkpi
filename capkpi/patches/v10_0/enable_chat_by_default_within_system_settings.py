from __future__ import unicode_literals

import capkpi


def execute():
	capkpi.reload_doctype("System Settings")
	doc = capkpi.get_single("System Settings")
	doc.enable_chat = 1

	# Changes prescribed by Nabin Hait (nabin@capkpi.com)
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_permissions = True

	doc.save()
