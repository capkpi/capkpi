# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import json
import unittest

import capkpi
from capkpi.website.doctype.web_form.web_form import accept
from capkpi.website.render import build_page

test_dependencies = ["Web Form"]


class TestWebForm(unittest.TestCase):
	def setUp(self):
		capkpi.conf.disable_website_cache = True
		capkpi.local.path = None

	def tearDown(self):
		capkpi.conf.disable_website_cache = False
		capkpi.local.path = None
		capkpi.local.request_ip = None
		capkpi.form_dict.web_form = None
		capkpi.form_dict.data = None
		capkpi.form_dict.docname = None

	def test_accept(self):
		capkpi.set_user("Administrator")

		doc = {
			"doctype": "Event",
			"subject": "_Test Event Web Form",
			"description": "_Test Event Description",
			"starts_on": "2014-09-09",
		}

		capkpi.form_dict.web_form = "manage-events"
		capkpi.form_dict.data = json.dumps(doc)
		capkpi.local.request_ip = "127.0.0.1"

		accept(web_form="manage-events", data=json.dumps(doc))

		self.event_name = capkpi.db.get_value("Event", {"subject": "_Test Event Web Form"})
		self.assertTrue(self.event_name)

	def test_edit(self):
		self.test_accept()

		doc = {
			"doctype": "Event",
			"subject": "_Test Event Web Form",
			"description": "_Test Event Description 1",
			"starts_on": "2014-09-09",
			"name": self.event_name,
		}

		self.assertNotEquals(
			capkpi.db.get_value("Event", self.event_name, "description"), doc.get("description")
		)

		capkpi.form_dict.web_form = "manage-events"
		capkpi.form_dict.docname = self.event_name
		capkpi.form_dict.data = json.dumps(doc)

		accept(web_form="manage-events", docname=self.event_name, data=json.dumps(doc))

		self.assertEqual(
			capkpi.db.get_value("Event", self.event_name, "description"), doc.get("description")
		)
