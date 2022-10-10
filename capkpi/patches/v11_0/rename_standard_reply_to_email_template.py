from __future__ import unicode_literals

import capkpi
from capkpi.model.rename_doc import rename_doc


def execute():
	if capkpi.db.table_exists("Standard Reply") and not capkpi.db.table_exists("Email Template"):
		rename_doc("DocType", "Standard Reply", "Email Template")
		capkpi.reload_doc("email", "doctype", "email_template")
