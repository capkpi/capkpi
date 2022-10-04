# Copyright (c) 2020, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi


def execute():
	capkpi.reload_doc("website", "doctype", "web_page_block")
	# remove unused templates
	capkpi.delete_doc("Web Template", "Navbar with Links on Right", force=1)
	capkpi.delete_doc("Web Template", "Footer Horizontal", force=1)
