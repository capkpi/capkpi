# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import capkpi


def execute():
	"""Add missing Twilio patch.

	While making Twilio as a standaone app, we missed to delete Twilio records from DB through migration. Adding the missing patch.
	"""
	capkpi.delete_doc_if_exists("DocType", "Twilio Number Group")
	if twilio_settings_doctype_in_integrations():
		capkpi.delete_doc_if_exists("DocType", "Twilio Settings")
		capkpi.db.sql("delete from `tabSingles` where `doctype`=%s", "Twilio Settings")


def twilio_settings_doctype_in_integrations() -> bool:
	"""Check Twilio Settings doctype exists in integrations module or not."""
	return capkpi.db.exists("DocType", {"name": "Twilio Settings", "module": "Integrations"})
