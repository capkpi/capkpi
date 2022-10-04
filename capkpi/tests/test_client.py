# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors

from __future__ import unicode_literals

import unittest

import capkpi


class TestClient(unittest.TestCase):
	def test_set_value(self):
		todo = capkpi.get_doc(dict(doctype="ToDo", description="test")).insert()
		capkpi.set_value("ToDo", todo.name, "description", "test 1")
		self.assertEqual(capkpi.get_value("ToDo", todo.name, "description"), "test 1")

		capkpi.set_value("ToDo", todo.name, {"description": "test 2"})
		self.assertEqual(capkpi.get_value("ToDo", todo.name, "description"), "test 2")

	def test_delete(self):
		from capkpi.client import delete

		todo = capkpi.get_doc(dict(doctype="ToDo", description="description")).insert()
		delete("ToDo", todo.name)

		self.assertFalse(capkpi.db.exists("ToDo", todo.name))
		self.assertRaises(capkpi.DoesNotExistError, delete, "ToDo", todo.name)

	def test_http_valid_method_access(self):
		from capkpi.client import delete
		from capkpi.handler import execute_cmd

		capkpi.set_user("Administrator")

		capkpi.local.request = capkpi._dict()
		capkpi.local.request.method = "POST"

		capkpi.local.form_dict = capkpi._dict(
			{"doc": dict(doctype="ToDo", description="Valid http method"), "cmd": "capkpi.client.save"}
		)
		todo = execute_cmd("capkpi.client.save")

		self.assertEqual(todo.get("description"), "Valid http method")

		delete("ToDo", todo.name)

	def test_http_invalid_method_access(self):
		from capkpi.handler import execute_cmd

		capkpi.set_user("Administrator")

		capkpi.local.request = capkpi._dict()
		capkpi.local.request.method = "GET"

		capkpi.local.form_dict = capkpi._dict(
			{"doc": dict(doctype="ToDo", description="Invalid http method"), "cmd": "capkpi.client.save"}
		)

		self.assertRaises(capkpi.PermissionError, execute_cmd, "capkpi.client.save")

	def test_run_doc_method(self):
		from capkpi.handler import execute_cmd

		if not capkpi.db.exists("Report", "Test Run Doc Method"):
			report = capkpi.get_doc(
				{
					"doctype": "Report",
					"ref_doctype": "User",
					"report_name": "Test Run Doc Method",
					"report_type": "Query Report",
					"is_standard": "No",
					"roles": [{"role": "System Manager"}],
				}
			).insert()
		else:
			report = capkpi.get_doc("Report", "Test Run Doc Method")

		capkpi.local.request = capkpi._dict()
		capkpi.local.request.method = "GET"

		# Whitelisted, works as expected
		capkpi.local.form_dict = capkpi._dict(
			{
				"dt": report.doctype,
				"dn": report.name,
				"method": "toggle_disable",
				"cmd": "run_doc_method",
				"args": 0,
			}
		)

		execute_cmd(capkpi.local.form_dict.cmd)

		# Not whitelisted, throws permission error
		capkpi.local.form_dict = capkpi._dict(
			{
				"dt": report.doctype,
				"dn": report.name,
				"method": "create_report_py",
				"cmd": "run_doc_method",
				"args": 0,
			}
		)

		self.assertRaises(capkpi.PermissionError, execute_cmd, capkpi.local.form_dict.cmd)

	def test_client_get(self):
		from capkpi.client import get

		todo = capkpi.get_doc(doctype="ToDo", description="test").insert()
		filters = {"name": todo.name}
		filters_json = capkpi.as_json(filters)

		self.assertEqual(get("ToDo", filters=filters).description, "test")
		self.assertEqual(get("ToDo", filters=filters_json).description, "test")
		self.assertEqual(get("System Settings", "", "").doctype, "System Settings")
		self.assertEqual(get("ToDo", filters={}), get("ToDo", filters="{}"))
		todo.delete()
