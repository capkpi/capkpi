from __future__ import unicode_literals

import capkpi
from capkpi.utils import cint


def execute():
	capkpi.reload_doctype("Dropbox Settings")
	check_dropbox_enabled = cint(capkpi.db.get_value("Dropbox Settings", None, "enabled"))
	if check_dropbox_enabled == 1:
		capkpi.db.set_value("Dropbox Settings", None, "file_backup", 1)
