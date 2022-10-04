# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import unittest

import capkpi
from capkpi.cache_manager import clear_controller_cache
from capkpi.desk.doctype.todo.todo import ToDo


class TestHooks(unittest.TestCase):
	def test_hooks(self):
		hooks = capkpi.get_hooks()
		self.assertTrue(isinstance(hooks.get("app_name"), list))
		self.assertTrue(isinstance(hooks.get("doc_events"), dict))
		self.assertTrue(isinstance(hooks.get("doc_events").get("*"), dict))
		self.assertTrue(isinstance(hooks.get("doc_events").get("*"), dict))
		self.assertTrue(
			"capkpi.desk.notifications.clear_doctype_notifications"
			in hooks.get("doc_events").get("*").get("on_update")
		)

	def test_override_doctype_class(self):
		from capkpi import hooks

		# Set hook
		hooks.override_doctype_class = {"ToDo": ["capkpi.tests.test_hooks.CustomToDo"]}

		# Clear cache
		capkpi.cache().delete_value("app_hooks")
		clear_controller_cache("ToDo")

		todo = capkpi.get_doc(doctype="ToDo", description="asdf")
		self.assertTrue(isinstance(todo, CustomToDo))

	def test_has_permission(self):
		from capkpi import hooks

		# Set hook
		address_has_permission_hook = hooks.has_permission.get("Address", [])
		if isinstance(address_has_permission_hook, str):
			address_has_permission_hook = [address_has_permission_hook]

		address_has_permission_hook.append("capkpi.tests.test_hooks.custom_has_permission")

		hooks.has_permission["Address"] = address_has_permission_hook

		# Clear cache
		capkpi.cache().delete_value("app_hooks")

		# Init User and Address
		username = "test@example.com"
		user = capkpi.get_doc("User", username)
		user.add_roles("System Manager")
		address = capkpi.new_doc("Address")

		# Test!
		self.assertTrue(capkpi.has_permission("Address", doc=address, user=username))

		address.flags.dont_touch_me = True
		self.assertFalse(capkpi.has_permission("Address", doc=address, user=username))


def custom_has_permission(doc, ptype, user):
	if doc.flags.dont_touch_me:
		return False


class CustomToDo(ToDo):
	pass
