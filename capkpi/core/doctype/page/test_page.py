# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import unittest

import capkpi

test_records = capkpi.get_test_records("Page")


class TestPage(unittest.TestCase):
	def test_naming(self):
		self.assertRaises(
			capkpi.NameError,
			capkpi.get_doc(dict(doctype="Page", page_name="DocType", module="Core")).insert,
		)
		self.assertRaises(
			capkpi.NameError,
			capkpi.get_doc(dict(doctype="Page", page_name="Settings", module="Core")).insert,
		)
