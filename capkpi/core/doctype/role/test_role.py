# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import unittest

import capkpi

test_records = capkpi.get_test_records("Role")


class TestUser(unittest.TestCase):
	def test_disable_role(self):
		capkpi.get_doc("User", "test@example.com").add_roles("_Test Role 3")

		role = capkpi.get_doc("Role", "_Test Role 3")
		role.disabled = 1
		role.save()

		self.assertTrue("_Test Role 3" not in capkpi.get_roles("test@example.com"))

		role = capkpi.get_doc("Role", "_Test Role 3")
		role.disabled = 0
		role.save()

		capkpi.get_doc("User", "test@example.com").add_roles("_Test Role 3")
		self.assertTrue("_Test Role 3" in capkpi.get_roles("test@example.com"))

	def test_change_desk_access(self):
		"""if we change desk acecss from role, remove from user"""
		capkpi.delete_doc_if_exists("User", "test-user-for-desk-access@example.com")
		capkpi.delete_doc_if_exists("Role", "desk-access-test")
		user = capkpi.get_doc(
			dict(doctype="User", email="test-user-for-desk-access@example.com", first_name="test")
		).insert()
		role = capkpi.get_doc(dict(doctype="Role", role_name="desk-access-test", desk_access=0)).insert()
		user.add_roles(role.name)
		user.save()
		self.assertTrue(user.user_type == "Website User")
		role.desk_access = 1
		role.save()
		user.reload()
		self.assertTrue(user.user_type == "System User")
		role.desk_access = 0
		role.save()
		user.reload()
		self.assertTrue(user.user_type == "Website User")
