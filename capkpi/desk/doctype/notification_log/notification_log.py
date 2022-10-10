# -*- coding: utf-8 -*-
# Copyright (c) 2019, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi import _
from capkpi.desk.doctype.notification_settings.notification_settings import (
	is_email_notifications_enabled_for_type,
	is_notifications_enabled,
	set_seen_value,
)
from capkpi.model.document import Document


class NotificationLog(Document):
	def after_insert(self):
		capkpi.publish_realtime("notification", after_commit=True, user=self.for_user)
		set_notifications_as_unseen(self.for_user)
		if is_email_notifications_enabled_for_type(self.for_user, self.type):
			try:
				send_notification_email(self)
			except capkpi.OutgoingEmailError:
				capkpi.log_error(message=capkpi.get_traceback(), title=_("Failed to send notification email"))


def get_permission_query_conditions(for_user):
	if not for_user:
		for_user = capkpi.session.user

	if for_user == "Administrator":
		return

	return """(`tabNotification Log`.for_user = {user})""".format(user=capkpi.db.escape(for_user))


def get_title(doctype, docname, title_field=None):
	if not title_field:
		title_field = capkpi.get_meta(doctype).get_title_field()
	title = docname if title_field == "name" else capkpi.db.get_value(doctype, docname, title_field)
	return title


def get_title_html(title):
	return '<b class="subject-title">{0}</b>'.format(title)


def enqueue_create_notification(users, doc):
	"""
	During installation of new site, enqueue_create_notification tries to connect to Redis.
	This breaks new site creation if Redis server is not running.
	We do not need any notifications in fresh installation
	"""
	if capkpi.flags.in_install:
		return

	doc = capkpi._dict(doc)

	if isinstance(users, capkpi.string_types):
		users = [user.strip() for user in users.split(",") if user.strip()]
	users = list(set(users))

	capkpi.enqueue(
		"capkpi.desk.doctype.notification_log.notification_log.make_notification_logs",
		doc=doc,
		users=users,
		now=capkpi.flags.in_test,
	)


def make_notification_logs(doc, users):
	from capkpi.social.doctype.energy_point_settings.energy_point_settings import (
		is_energy_point_enabled,
	)

	for user in users:
		if capkpi.db.exists("User", {"email": user, "enabled": 1}):
			if is_notifications_enabled(user):
				if doc.type == "Energy Point" and not is_energy_point_enabled():
					return

				_doc = capkpi.new_doc("Notification Log")
				_doc.update(doc)
				_doc.for_user = user
				if _doc.for_user != _doc.from_user or doc.type == "Energy Point" or doc.type == "Alert":
					_doc.insert(ignore_permissions=True)


def send_notification_email(doc):

	if doc.type == "Energy Point" and doc.email_content is None:
		return

	from capkpi.utils import get_url_to_form, strip_html

	doc_link = get_url_to_form(doc.document_type, doc.document_name)
	header = get_email_header(doc)
	email_subject = strip_html(doc.subject)

	capkpi.sendmail(
		recipients=doc.for_user,
		subject=email_subject,
		template="new_notification",
		args={
			"body_content": doc.subject,
			"description": doc.email_content,
			"document_type": doc.document_type,
			"document_name": doc.document_name,
			"doc_link": doc_link,
		},
		header=[header, "orange"],
		now=capkpi.flags.in_test,
	)


def get_email_header(doc):
	docname = doc.document_name
	header_map = {
		"Default": _("New Notification"),
		"Mention": _("New Mention on {0}").format(docname),
		"Assignment": _("Assignment Update on {0}").format(docname),
		"Share": _("New Document Shared {0}").format(docname),
		"Energy Point": _("Energy Point Update on {0}").format(docname),
	}

	return header_map[doc.type or "Default"]


@capkpi.whitelist()
def mark_all_as_read():
	unread_docs_list = capkpi.db.get_all(
		"Notification Log", filters={"read": 0, "for_user": capkpi.session.user}
	)
	unread_docnames = [doc.name for doc in unread_docs_list]
	if unread_docnames:
		filters = {"name": ["in", unread_docnames]}
		capkpi.db.set_value("Notification Log", filters, "read", 1, update_modified=False)


@capkpi.whitelist()
def mark_as_read(docname):
	if docname:
		capkpi.db.set_value("Notification Log", docname, "read", 1, update_modified=False)


@capkpi.whitelist()
def trigger_indicator_hide():
	capkpi.publish_realtime("indicator_hide", user=capkpi.session.user)


def set_notifications_as_unseen(user):
	try:
		capkpi.db.set_value("Notification Settings", user, "seen", 0, update_modified=False)
	except capkpi.DoesNotExistError:
		return
