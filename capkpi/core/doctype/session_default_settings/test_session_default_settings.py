# -*- coding: utf-8 -*-
# Copyright (c) 2019, CapKPI Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import unittest

import capkpi
from capkpi.core.doctype.session_default_settings.session_default_settings import (
	clear_session_defaults,
	set_session_default_values,
)


class TestSessionDefaultSettings(unittest.TestCase):
	def test_set_session_default_settings(self):
		capkpi.set_user("Administrator")
		settings = capkpi.get_single("Session Default Settings")
		settings.session_defaults = []
		settings.append("session_defaults", {"ref_doctype": "Role"})
		settings.save()

		set_session_default_values({"role": "Website Manager"})

		todo = capkpi.get_doc(
			dict(doctype="ToDo", description="test session defaults set", assigned_by="Administrator")
		).insert()
		self.assertEqual(todo.role, "Website Manager")

	def test_clear_session_defaults(self):
		clear_session_defaults()
		todo = capkpi.get_doc(
			dict(doctype="ToDo", description="test session defaults cleared", assigned_by="Administrator")
		).insert()
		self.assertNotEqual(todo.role, "Website Manager")
