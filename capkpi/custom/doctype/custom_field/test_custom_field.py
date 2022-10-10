#  -*- coding: utf-8 -*-

# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# See license.txt

from __future__ import unicode_literals

import unittest

import capkpi

test_records = capkpi.get_test_records("Custom Field")


class TestCustomField(unittest.TestCase):
	def test_create_custom_fields(self):
		from .custom_field import create_custom_fields

		create_custom_fields(
			{
				"Address": [
					{
						"fieldname": "_test_custom_field_1",
						"label": "_Test Custom Field 1",
						"fieldtype": "Data",
						"insert_after": "phone",
					},
				],
				("Address", "Contact"): [
					{
						"fieldname": "_test_custom_field_2",
						"label": "_Test Custom Field 2",
						"fieldtype": "Data",
						"insert_after": "phone",
					},
				],
			}
		)

		capkpi.db.commit()

		self.assertTrue(capkpi.db.exists("Custom Field", "Address-_test_custom_field_1"))
		self.assertTrue(capkpi.db.exists("Custom Field", "Address-_test_custom_field_2"))
		self.assertTrue(capkpi.db.exists("Custom Field", "Contact-_test_custom_field_2"))
