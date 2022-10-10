# -*- coding: utf-8 -*-
# Copyright (c) 2018, CapKPI Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import hashlib
import unittest

import capkpi

test_records = []


class TestTransactionLog(unittest.TestCase):
	def test_validate_chaining(self):
		capkpi.get_doc(
			{
				"doctype": "Transaction Log",
				"reference_doctype": "Test Doctype",
				"document_name": "Test Document 1",
				"data": "first_data",
			}
		).insert(ignore_permissions=True)

		second_log = capkpi.get_doc(
			{
				"doctype": "Transaction Log",
				"reference_doctype": "Test Doctype",
				"document_name": "Test Document 2",
				"data": "second_data",
			}
		).insert(ignore_permissions=True)

		third_log = capkpi.get_doc(
			{
				"doctype": "Transaction Log",
				"reference_doctype": "Test Doctype",
				"document_name": "Test Document 3",
				"data": "third_data",
			}
		).insert(ignore_permissions=True)

		sha = hashlib.sha256()
		sha.update(
			capkpi.safe_encode(str(third_log.transaction_hash))
			+ capkpi.safe_encode(str(second_log.chaining_hash))
		)

		self.assertEqual(sha.hexdigest(), third_log.chaining_hash)
