# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import unittest

import capkpi
import capkpi.desk.form.assign_to
from capkpi.automation.doctype.assignment_rule.test_assignment_rule import make_note
from capkpi.desk.form.load import get_assignments
from capkpi.desk.listview import get_group_by_count


class TestAssign(unittest.TestCase):
	def test_assign(self):
		todo = capkpi.get_doc({"doctype": "ToDo", "description": "test"}).insert()
		if not capkpi.db.exists("User", "test@example.com"):
			capkpi.get_doc({"doctype": "User", "email": "test@example.com", "first_name": "Test"}).insert()

		added = assign(todo, "test@example.com")

		self.assertTrue("test@example.com" in [d.owner for d in added])

		removed = capkpi.desk.form.assign_to.remove(todo.doctype, todo.name, "test@example.com")

		# assignment is cleared
		assignments = capkpi.desk.form.assign_to.get(dict(doctype=todo.doctype, name=todo.name))
		self.assertEqual(len(assignments), 0)

	def test_assignment_count(self):
		capkpi.db.sql("delete from tabToDo")

		if not capkpi.db.exists("User", "test_assign1@example.com"):
			capkpi.get_doc(
				{
					"doctype": "User",
					"email": "test_assign1@example.com",
					"first_name": "Test",
					"roles": [{"role": "System Manager"}],
				}
			).insert()

		if not capkpi.db.exists("User", "test_assign2@example.com"):
			capkpi.get_doc(
				{
					"doctype": "User",
					"email": "test_assign2@example.com",
					"first_name": "Test",
					"roles": [{"role": "System Manager"}],
				}
			).insert()

		note = make_note()
		assign(note, "test_assign1@example.com")

		note = make_note(dict(public=1))
		assign(note, "test_assign2@example.com")

		note = make_note(dict(public=1))
		assign(note, "test_assign2@example.com")

		note = make_note()
		assign(note, "test_assign2@example.com")

		data = {d.name: d.count for d in get_group_by_count("Note", "[]", "assigned_to")}

		self.assertTrue("test_assign1@example.com" in data)
		self.assertEqual(data["test_assign1@example.com"], 1)
		self.assertEqual(data["test_assign2@example.com"], 3)

		data = {d.name: d.count for d in get_group_by_count("Note", '[{"public": 1}]', "assigned_to")}

		self.assertFalse("test_assign1@example.com" in data)
		self.assertEqual(data["test_assign2@example.com"], 2)

		capkpi.db.rollback()

	def test_assignment_removal(self):
		todo = capkpi.get_doc({"doctype": "ToDo", "description": "test"}).insert()
		if not capkpi.db.exists("User", "test@example.com"):
			capkpi.get_doc({"doctype": "User", "email": "test@example.com", "first_name": "Test"}).insert()

		new_todo = assign(todo, "test@example.com")

		# remove assignment
		capkpi.db.set_value("ToDo", new_todo[0].name, "owner", "")

		self.assertFalse(get_assignments("ToDo", todo.name))


def assign(doc, user):
	return capkpi.desk.form.assign_to.add(
		{
			"assign_to": [user],
			"doctype": doc.doctype,
			"name": doc.name,
			"description": "test",
		}
	)
