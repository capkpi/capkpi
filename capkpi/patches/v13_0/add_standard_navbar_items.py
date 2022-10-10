from __future__ import unicode_literals

import capkpi
from capkpi.utils.install import add_standard_navbar_items


def execute():
	# Add standard navbar items for ERP in Navbar Settings
	capkpi.reload_doc("core", "doctype", "navbar_settings")
	capkpi.reload_doc("core", "doctype", "navbar_item")
	add_standard_navbar_items()
