from __future__ import unicode_literals

import json

import capkpi
from capkpi.config import get_modules_from_all_apps_for_user
from capkpi.desk.moduleview import get_onboard_items


def execute():
	"""Reset the initial customizations for desk, with modules, indices and links."""
	capkpi.reload_doc("core", "doctype", "user")
	capkpi.db.sql("""update tabUser set home_settings = ''""")
