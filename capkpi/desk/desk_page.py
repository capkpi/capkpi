# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi
from capkpi.translate import send_translations


@capkpi.whitelist()
def get(name):
	"""
	Return the :term:`doclist` of the `Page` specified by `name`
	"""
	page = capkpi.get_doc("Page", name)
	if page.is_permitted():
		page.load_assets()
		docs = capkpi._dict(page.as_dict())
		if getattr(page, "_dynamic_page", None):
			docs["_dynamic_page"] = 1

		return docs
	else:
		capkpi.response["403"] = 1
		raise capkpi.PermissionError("No read permission for Page %s" % (page.title or name))


@capkpi.whitelist(allow_guest=True)
def getpage():
	"""
	Load the page from `capkpi.form` and send it via `capkpi.response`
	"""
	page = capkpi.form_dict.get("name")
	doc = get(page)

	# load translations
	if capkpi.lang != "en":
		send_translations(capkpi.get_lang_dict("page", page))

	capkpi.response.docs.append(doc)


def has_permission(page):
	if capkpi.session.user == "Administrator" or "System Manager" in capkpi.get_roles():
		return True

	page_roles = [d.role for d in page.get("roles")]
	if page_roles:
		if capkpi.session.user == "Guest" and "Guest" not in page_roles:
			return False
		elif not set(page_roles).intersection(set(capkpi.get_roles())):
			# check if roles match
			return False

	if not capkpi.has_permission("Page", ptype="read", doc=page):
		# check if there are any user_permissions
		return False
	else:
		# hack for home pages! if no Has Roles, allow everyone to see!
		return True
