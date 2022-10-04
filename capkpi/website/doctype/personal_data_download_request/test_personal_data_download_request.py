# -*- coding: utf-8 -*-
# Copyright (c) 2019, CapKPI Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import json

import capkpi
from capkpi.contacts.doctype.contact.contact import get_contact_name
from capkpi.core.doctype.user.user import create_contact
from capkpi.tests.utils import CapKPITestCase
from capkpi.website.doctype.personal_data_download_request.personal_data_download_request import (
	get_user_data,
)


class TestRequestPersonalData(CapKPITestCase):
	def setUp(self):
		create_user_if_not_exists(email="test_privacy@example.com")

	def tearDown(self):
		capkpi.db.sql("""DELETE FROM `tabPersonal Data Download Request`""")

	def test_user_data_creation(self):
		user_data = json.loads(get_user_data("test_privacy@example.com"))
		contact_name = get_contact_name("test_privacy@example.com")
		expected_data = {"Contact": capkpi.get_all("Contact", {"name": contact_name}, ["*"])}
		expected_data = json.loads(json.dumps(expected_data, default=str))
		self.assertEqual({"Contact": user_data["Contact"]}, expected_data)

	def test_file_and_email_creation(self):
		capkpi.set_user("test_privacy@example.com")
		download_request = capkpi.get_doc(
			{"doctype": "Personal Data Download Request", "user": "test_privacy@example.com"}
		)
		download_request.save(ignore_permissions=True)

		capkpi.set_user("Administrator")

		file_count = capkpi.db.count(
			"File",
			{
				"attached_to_doctype": "Personal Data Download Request",
				"attached_to_name": download_request.name,
			},
		)

		self.assertEqual(file_count, 1)

		email_queue = capkpi.get_all(
			"Email Queue", fields=["message"], order_by="creation DESC", limit=1
		)
		self.assertIn(capkpi._("Download Your Data"), email_queue[0].message)

		capkpi.db.sql("delete from `tabEmail Queue`")


def create_user_if_not_exists(email, first_name=None):
	capkpi.delete_doc_if_exists("User", email)

	user = capkpi.get_doc(
		{
			"doctype": "User",
			"user_type": "Website User",
			"email": email,
			"send_welcome_email": 0,
			"first_name": first_name or email.split("@")[0],
			"birth_date": capkpi.utils.now_datetime(),
		}
	).insert(ignore_permissions=True)
	create_contact(user=user)
