# -*- coding: utf-8 -*-
# Copyright (c) 2019, CapKPI Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import unittest

import requests

import capkpi
from capkpi.utils import get_site_url

scripts = [
	dict(
		name="test_todo",
		script_type="DocType Event",
		doctype_event="Before Insert",
		reference_doctype="ToDo",
		script="""
if "test" in doc.description:
	doc.status = 'Closed'
""",
	),
	dict(
		name="test_todo_validate",
		script_type="DocType Event",
		doctype_event="Before Insert",
		reference_doctype="ToDo",
		script="""
if "validate" in doc.description:
	raise capkpi.ValidationError
""",
	),
	dict(
		name="test_api",
		script_type="API",
		api_method="test_server_script",
		allow_guest=1,
		script="""
capkpi.response['message'] = 'hello'
""",
	),
	dict(
		name="test_return_value",
		script_type="API",
		api_method="test_return_value",
		allow_guest=1,
		script="""
capkpi.flags = 'hello'
""",
	),
	dict(
		name="test_permission_query",
		script_type="Permission Query",
		reference_doctype="ToDo",
		script="""
conditions = '1 = 1'
""",
	),
	dict(
		name="test_invalid_namespace_method",
		script_type="DocType Event",
		doctype_event="Before Insert",
		reference_doctype="Note",
		script="""
capkpi.method_that_doesnt_exist("do some magic")
""",
	),
	dict(
		name="test_todo_commit",
		script_type="DocType Event",
		doctype_event="Before Save",
		reference_doctype="ToDo",
		disabled=1,
		script="""
capkpi.db.commit()
""",
	),
]


class TestServerScript(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		capkpi.db.commit()
		capkpi.db.sql("truncate `tabServer Script`")
		capkpi.get_doc("User", "Administrator").add_roles("Script Manager")
		for script in scripts:
			script_doc = capkpi.get_doc(doctype="Server Script")
			script_doc.update(script)
			script_doc.insert()

		capkpi.db.commit()

	@classmethod
	def tearDownClass(cls):
		capkpi.db.commit()
		capkpi.db.sql("truncate `tabServer Script`")
		capkpi.cache().delete_value("server_script_map")

	def setUp(self):
		capkpi.cache().delete_value("server_script_map")

	def test_doctype_event(self):
		todo = capkpi.get_doc(dict(doctype="ToDo", description="hello")).insert()
		self.assertEqual(todo.status, "Open")

		todo = capkpi.get_doc(dict(doctype="ToDo", description="test todo")).insert()
		self.assertEqual(todo.status, "Closed")

		self.assertRaises(
			capkpi.ValidationError, capkpi.get_doc(dict(doctype="ToDo", description="validate me")).insert
		)

	def test_api(self):
		response = requests.post(get_site_url(capkpi.local.site) + "/api/method/test_server_script")
		self.assertEqual(response.status_code, 200)
		self.assertEqual("hello", response.json()["message"])

	def test_api_return(self):
		self.assertEqual(capkpi.get_doc("Server Script", "test_return_value").execute_method(), "hello")

	def test_permission_query(self):
		self.assertTrue("where (1 = 1)" in capkpi.db.get_list("ToDo", return_query=1))
		self.assertTrue(isinstance(capkpi.db.get_list("ToDo"), list))

	def test_attribute_error(self):
		"""Raise AttributeError if method not found in Namespace"""
		note = capkpi.get_doc({"doctype": "Note", "title": "Test Note: Server Script"})
		self.assertRaises(AttributeError, note.insert)

	def test_syntax_validation(self):
		server_script = scripts[0]
		server_script["script"] = "js || code.?"

		with self.assertRaises(capkpi.ValidationError) as se:
			capkpi.get_doc(doctype="Server Script", **server_script).insert()

		self.assertTrue(
			"invalid python code" in str(se.exception).lower(), msg="Python code validation not working"
		)

	def test_commit_in_doctype_event(self):
		server_script = capkpi.get_doc("Server Script", "test_todo_commit")
		server_script.disabled = 0
		server_script.save()

		self.assertRaises(
			AttributeError, capkpi.get_doc(dict(doctype="ToDo", description="test me")).insert
		)

		server_script.disabled = 1
		server_script.save()

	def test_restricted_qb(self):
		todo = capkpi.get_doc(doctype="ToDo", description="QbScriptTestNote")
		todo.insert()

		script = capkpi.get_doc(
			doctype="Server Script",
			name="test_qb_restrictions",
			script_type="API",
			api_method="test_qb_restrictions",
			allow_guest=1,
			# whitelisted update
			script=f"""
capkpi.db.set_value("ToDo", "{todo.name}", "description", "safe")
""",
		)
		script.insert()
		script.execute_method()

		todo.reload()
		self.assertEqual(todo.description, "safe")

		# unsafe update
		script.script = f"""
todo = capkpi.qb.DocType("ToDo")
capkpi.qb.update(todo).set(todo.description, "unsafe").where(todo.name == "{todo.name}").run()
"""
		script.save()
		self.assertRaises(capkpi.PermissionError, script.execute_method)
		todo.reload()
		self.assertEqual(todo.description, "safe")

		# safe select
		script.script = f"""
todo = capkpi.qb.DocType("ToDo")
capkpi.qb.from_(todo).select(todo.name).where(todo.name == "{todo.name}").run()
"""
		script.save()
		script.execute_method()
