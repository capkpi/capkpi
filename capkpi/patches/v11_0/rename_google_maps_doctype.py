from __future__ import unicode_literals

import capkpi
from capkpi.model.rename_doc import rename_doc


def execute():
	if capkpi.db.exists("DocType", "Google Maps") and not capkpi.db.exists(
		"DocType", "Google Maps Settings"
	):
		rename_doc("DocType", "Google Maps", "Google Maps Settings")
