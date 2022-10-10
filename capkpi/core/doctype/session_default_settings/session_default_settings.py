# -*- coding: utf-8 -*-
# Copyright (c) 2019, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json

import capkpi
from capkpi import _
from capkpi.model.document import Document


class SessionDefaultSettings(Document):
	pass


@capkpi.whitelist()
def get_session_default_values():
	settings = capkpi.get_single("Session Default Settings")
	fields = []
	for default_values in settings.session_defaults:
		reference_doctype = capkpi.scrub(default_values.ref_doctype)
		fields.append(
			{
				"fieldname": reference_doctype,
				"fieldtype": "Link",
				"options": default_values.ref_doctype,
				"label": _("Default {0}").format(_(default_values.ref_doctype)),
				"default": capkpi.defaults.get_user_default(reference_doctype),
			}
		)
	return json.dumps(fields)


@capkpi.whitelist()
def set_session_default_values(default_values):
	default_values = capkpi.parse_json(default_values)
	for entry in default_values:
		try:
			capkpi.defaults.set_user_default(entry, default_values.get(entry))
		except Exception:
			return
	return "success"


# called on hook 'on_logout' to clear defaults for the session
def clear_session_defaults():
	settings = capkpi.get_single("Session Default Settings").session_defaults
	for entry in settings:
		capkpi.defaults.clear_user_default(capkpi.scrub(entry.ref_doctype))
