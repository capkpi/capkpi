# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# License: See license.txt

from __future__ import unicode_literals

from six import string_types

import capkpi
import capkpi.permissions
from capkpi import _
from capkpi.core.doctype.activity_log.activity_log import add_authentication_log
from capkpi.utils import get_fullname


def update_feed(doc, method=None):
	if capkpi.flags.in_patch or capkpi.flags.in_install or capkpi.flags.in_import:
		return

	if doc._action != "save" or doc.flags.ignore_feed:
		return

	if doc.doctype == "Activity Log" or doc.meta.issingle:
		return

	if hasattr(doc, "get_feed"):
		feed = doc.get_feed()

		if feed:
			if isinstance(feed, string_types):
				feed = {"subject": feed}

			feed = capkpi._dict(feed)
			doctype = feed.doctype or doc.doctype
			name = feed.name or doc.name

			# delete earlier feed
			capkpi.db.sql(
				"""delete from `tabActivity Log`
				where
					reference_doctype=%s and reference_name=%s
					and link_doctype=%s""",
				(doctype, name, feed.link_doctype),
			)
			capkpi.get_doc(
				{
					"doctype": "Activity Log",
					"reference_doctype": doctype,
					"reference_name": name,
					"subject": feed.subject,
					"full_name": get_fullname(doc.owner),
					"reference_owner": capkpi.db.get_value(doctype, name, "owner"),
					"link_doctype": feed.link_doctype,
					"link_name": feed.link_name,
				}
			).insert(ignore_permissions=True)


def login_feed(login_manager):
	if login_manager.user != "Guest":
		subject = _("{0} logged in").format(get_fullname(login_manager.user))
		add_authentication_log(subject, login_manager.user)


def logout_feed(user, reason):
	if user and user != "Guest":
		subject = _("{0} logged out: {1}").format(get_fullname(user), capkpi.bold(reason))
		add_authentication_log(subject, user, operation="Logout")


def get_feed_match_conditions(user=None, doctype="Comment"):
	if not user:
		user = capkpi.session.user

	conditions = [
		"`tab{doctype}`.owner={user} or `tab{doctype}`.reference_owner={user}".format(
			user=capkpi.db.escape(user), doctype=doctype
		)
	]

	user_permissions = capkpi.permissions.get_user_permissions(user)
	can_read = capkpi.get_user().get_can_read()

	can_read_doctypes = [
		"'{}'".format(dt) for dt in list(set(can_read) - set(list(user_permissions)))
	]

	if can_read_doctypes:
		conditions += [
			"""(`tab{doctype}`.reference_doctype is null
			or `tab{doctype}`.reference_doctype = ''
			or `tab{doctype}`.reference_doctype
			in ({values}))""".format(
				doctype=doctype, values=", ".join(can_read_doctypes)
			)
		]

		if user_permissions:
			can_read_docs = []
			for dt, obj in user_permissions.items():
				for n in obj:
					can_read_docs.append("{}|{}".format(capkpi.db.escape(dt), capkpi.db.escape(n.get("doc", ""))))

			if can_read_docs:
				conditions.append(
					"concat_ws('|', `tab{doctype}`.reference_doctype, `tab{doctype}`.reference_name) in ({values})".format(
						doctype=doctype, values=", ".join(can_read_docs)
					)
				)

	return "(" + " or ".join(conditions) + ")"
