# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import unittest

import capkpi


class TestDocumentLocks(unittest.TestCase):
	def test_locking(self):
		todo = capkpi.get_doc(dict(doctype="ToDo", description="test")).insert()
		todo_1 = capkpi.get_doc("ToDo", todo.name)

		todo.lock()
		self.assertRaises(capkpi.DocumentLockedError, todo_1.lock)
		todo.unlock()

		todo_1.lock()
		self.assertRaises(capkpi.DocumentLockedError, todo.lock)
		todo_1.unlock()
