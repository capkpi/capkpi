# -*- coding: utf-8 -*-
# Copyright (c) 2019, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi.model.document import Document


class NotificationSettings(Document):
	def on_update(self):
		from capkpi.desk.notifications import clear_notification_config

		clear_notification_config(capkpi.session.user)


def is_notifications_enabled(user):
	enabled = capkpi.db.get_value("Notification Settings", user, "enabled")
	if enabled is None:
		return True
	return enabled


def is_email_notifications_enabled(user):
	enabled = capkpi.db.get_value("Notification Settings", user, "enable_email_notifications")
	if enabled is None:
		return True
	return enabled


def is_email_notifications_enabled_for_type(user, notification_type):
	if not is_email_notifications_enabled(user):
		return False

	if notification_type == "Alert":
		return False

	fieldname = "enable_email_" + capkpi.scrub(notification_type)
	enabled = capkpi.db.get_value("Notification Settings", user, fieldname)
	if enabled is None:
		return True
	return enabled


def create_notification_settings(user):
	if not capkpi.db.exists("Notification Settings", user):
		_doc = capkpi.new_doc("Notification Settings")
		_doc.name = user
		_doc.insert(ignore_permissions=True)


def toggle_notifications(user: str, enable: bool = False):
	try:
		settings = capkpi.get_doc("Notification Settings", user)
	except capkpi.DoesNotExistError:
		capkpi.clear_last_message()
		return

	if settings.enabled != enable:
		settings.enabled = enable
		settings.save()


@capkpi.whitelist()
def get_subscribed_documents():
	if not capkpi.session.user:
		return []

	try:
		if capkpi.db.exists("Notification Settings", capkpi.session.user):
			doc = capkpi.get_doc("Notification Settings", capkpi.session.user)
			return [item.document for item in doc.subscribed_documents]
	# Notification Settings is fetched even before sync doctype is called
	# but it will throw an ImportError, we can ignore it in migrate
	except ImportError:
		pass

	return []


def get_permission_query_conditions(user):
	if not user:
		user = capkpi.session.user

	if user == "Administrator":
		return

	roles = capkpi.get_roles(user)
	if "System Manager" in roles:
		return """(`tabNotification Settings`.name != 'Administrator')"""

	return """(`tabNotification Settings`.name = {user})""".format(user=capkpi.db.escape(user))


@capkpi.whitelist()
def set_seen_value(value, user):
	capkpi.db.set_value("Notification Settings", user, "seen", value, update_modified=False)
