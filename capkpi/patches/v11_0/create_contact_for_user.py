from __future__ import unicode_literals

import re

import capkpi
from capkpi.core.doctype.user.user import create_contact


def execute():
	"""Create Contact for each User if not present"""
	capkpi.reload_doc("integrations", "doctype", "google_contacts")
	capkpi.reload_doc("contacts", "doctype", "contact")
	capkpi.reload_doc("core", "doctype", "dynamic_link")

	contact_meta = capkpi.get_meta("Contact")
	if contact_meta.has_field("phone_nos") and contact_meta.has_field("email_ids"):
		capkpi.reload_doc("contacts", "doctype", "contact_phone")
		capkpi.reload_doc("contacts", "doctype", "contact_email")

	users = capkpi.get_all("User", filters={"name": ("not in", "Administrator, Guest")}, fields=["*"])
	for user in users:
		if capkpi.db.exists("Contact", {"email_id": user.email}) or capkpi.db.exists(
			"Contact Email", {"email_id": user.email}
		):
			continue
		if user.first_name:
			user.first_name = re.sub("[<>]+", "", capkpi.safe_decode(user.first_name))
		if user.last_name:
			user.last_name = re.sub("[<>]+", "", capkpi.safe_decode(user.last_name))
		create_contact(user, ignore_links=True, ignore_mandatory=True)
