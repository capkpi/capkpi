# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import capkpi


def execute():
	capkpi.reload_doc("core", "doctype", "system_settings", force=1)
	capkpi.db.set_value("System Settings", None, "password_reset_limit", 3)
