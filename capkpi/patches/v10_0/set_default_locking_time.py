# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi


def execute():
	capkpi.reload_doc("core", "doctype", "system_settings")
	capkpi.db.set_value("System Settings", None, "allow_login_after_fail", 60)
