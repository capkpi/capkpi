# -*- coding: utf-8 -*-
# Copyright (c) 2018, CapKPI Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import unittest

import capkpi


class TestViewLog(unittest.TestCase):
	def tearDown(self):
		capkpi.set_user("Administrator")

	def test_if_user_is_added(self):
		ev = capkpi.get_doc(
			{
				"doctype": "Event",
				"subject": "test event for view logs",
				"starts_on": "2018-06-04 14:11:00",
				"event_type": "Public",
			}
		).insert()

		capkpi.set_user("test@example.com")

		from capkpi.desk.form.load import getdoc

		# load the form
		getdoc("Event", ev.name)
		a = capkpi.get_value(
			doctype="View Log",
			filters={"reference_doctype": "Event", "reference_name": ev.name},
			fieldname=["viewed_by"],
		)

		self.assertEqual("test@example.com", a)
		self.assertNotEqual("test1@example.com", a)
