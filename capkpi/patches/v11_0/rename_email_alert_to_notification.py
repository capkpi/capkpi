from __future__ import unicode_literals

import capkpi
from capkpi.model.rename_doc import rename_doc


def execute():
	if capkpi.db.table_exists("Email Alert Recipient") and not capkpi.db.table_exists(
		"Notification Recipient"
	):
		rename_doc("DocType", "Email Alert Recipient", "Notification Recipient")
		capkpi.reload_doc("email", "doctype", "notification_recipient")

	if capkpi.db.table_exists("Email Alert") and not capkpi.db.table_exists("Notification"):
		rename_doc("DocType", "Email Alert", "Notification")
		capkpi.reload_doc("email", "doctype", "notification")
