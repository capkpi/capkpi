# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi import _
from capkpi.model import no_value_fields
from capkpi.model.document import Document
from capkpi.translate import set_default_language
from capkpi.twofactor import toggle_two_factor_auth
from capkpi.utils import cint, today
from capkpi.utils.momentjs import get_all_timezones


class SystemSettings(Document):
	def validate(self):
		enable_password_policy = cint(self.enable_password_policy) and True or False
		minimum_password_score = cint(getattr(self, "minimum_password_score", 0)) or 0
		if enable_password_policy and minimum_password_score <= 0:
			capkpi.throw(_("Please select Minimum Password Score"))
		elif not enable_password_policy:
			self.minimum_password_score = ""

		for key in ("session_expiry", "session_expiry_mobile"):
			if self.get(key):
				parts = self.get(key).split(":")
				if len(parts) != 2 or not (cint(parts[0]) or cint(parts[1])):
					capkpi.throw(_("Session Expiry must be in format {0}").format("hh:mm"))

		if self.enable_two_factor_auth:
			if self.two_factor_method == "SMS":
				if not capkpi.db.get_value("SMS Settings", None, "sms_gateway_url"):
					capkpi.throw(
						_("Please setup SMS before setting it as an authentication method, via SMS Settings")
					)
			toggle_two_factor_auth(True, roles=["All"])
		else:
			self.bypass_2fa_for_retricted_ip_users = 0
			self.bypass_restrict_ip_check_if_2fa_enabled = 0

		capkpi.flags.update_last_reset_password_date = False
		if self.force_user_to_reset_password and not cint(
			capkpi.db.get_single_value("System Settings", "force_user_to_reset_password")
		):
			capkpi.flags.update_last_reset_password_date = True

	def on_update(self):
		self.set_defaults()

		capkpi.cache().delete_value("system_settings")
		capkpi.cache().delete_value("time_zone")
		capkpi.local.system_settings = {}

		if capkpi.flags.update_last_reset_password_date:
			update_last_reset_password_date()

	def set_defaults(self):
		for df in self.meta.get("fields"):
			if df.fieldtype not in no_value_fields and self.has_value_changed(df.fieldname):
				capkpi.db.set_default(df.fieldname, self.get(df.fieldname))

		if self.language:
			set_default_language(self.language)


def update_last_reset_password_date():
	capkpi.db.sql(
		""" UPDATE `tabUser`
		SET
			last_password_reset_date = %s
		WHERE
			last_password_reset_date is null""",
		today(),
	)


@capkpi.whitelist()
def load():
	if not "System Manager" in capkpi.get_roles():
		capkpi.throw(_("Not permitted"), capkpi.PermissionError)

	all_defaults = capkpi.db.get_defaults()
	defaults = {}

	for df in capkpi.get_meta("System Settings").get("fields"):
		if df.fieldtype in ("Select", "Data"):
			defaults[df.fieldname] = all_defaults.get(df.fieldname)

	return {"timezones": get_all_timezones(), "defaults": defaults}
