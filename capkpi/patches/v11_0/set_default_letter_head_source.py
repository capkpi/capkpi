from __future__ import unicode_literals

import capkpi


def execute():
	capkpi.reload_doctype("Letter Head")

	# source of all existing letter heads must be HTML
	capkpi.db.sql("update `tabLetter Head` set source = 'HTML'")
