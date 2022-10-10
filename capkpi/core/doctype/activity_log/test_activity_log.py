# -*- coding: utf-8 -*-
# Copyright (c) 2015, CapKPI Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import time
import unittest

import capkpi
from capkpi.auth import CookieManager, LoginManager


class TestActivityLog(unittest.TestCase):
	def test_activity_log(self):

		# test user login log
		capkpi.local.form_dict = capkpi._dict(
			{
				"cmd": "login",
				"sid": "Guest",
				"pwd": capkpi.conf.admin_password or "admin",
				"usr": "Administrator",
			}
		)

		capkpi.local.cookie_manager = CookieManager()
		capkpi.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertFalse(capkpi.form_dict.pwd)
		self.assertEqual(auth_log.status, "Success")

		# test user logout log
		capkpi.local.login_manager.logout()
		auth_log = self.get_auth_log(operation="Logout")
		self.assertEqual(auth_log.status, "Success")

		# test invalid login
		capkpi.form_dict.update({"pwd": "password"})
		self.assertRaises(capkpi.AuthenticationError, LoginManager)
		auth_log = self.get_auth_log()
		self.assertEqual(auth_log.status, "Failed")

		capkpi.local.form_dict = capkpi._dict()

	def get_auth_log(self, operation="Login"):
		names = capkpi.db.get_all(
			"Activity Log",
			filters={
				"user": "Administrator",
				"operation": operation,
			},
			order_by="`creation` DESC",
		)

		name = names[0]
		auth_log = capkpi.get_doc("Activity Log", name)
		return auth_log

	def test_brute_security(self):
		update_system_settings({"allow_consecutive_login_attempts": 3, "allow_login_after_fail": 5})

		capkpi.local.form_dict = capkpi._dict(
			{"cmd": "login", "sid": "Guest", "pwd": "admin", "usr": "Administrator"}
		)

		capkpi.local.cookie_manager = CookieManager()
		capkpi.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertEquals(auth_log.status, "Success")

		# test user logout log
		capkpi.local.login_manager.logout()
		auth_log = self.get_auth_log(operation="Logout")
		self.assertEquals(auth_log.status, "Success")

		# test invalid login
		capkpi.form_dict.update({"pwd": "password"})
		self.assertRaises(capkpi.AuthenticationError, LoginManager)
		self.assertRaises(capkpi.AuthenticationError, LoginManager)
		self.assertRaises(capkpi.AuthenticationError, LoginManager)

		# REMOVE ME: current logic allows allow_consecutive_login_attempts+1 attempts
		# before raising security exception, remove below line when that is fixed.
		self.assertRaises(capkpi.AuthenticationError, LoginManager)
		self.assertRaises(capkpi.SecurityException, LoginManager)
		time.sleep(5)
		self.assertRaises(capkpi.AuthenticationError, LoginManager)

		capkpi.local.form_dict = capkpi._dict()


def update_system_settings(args):
	doc = capkpi.get_doc("System Settings")
	doc.update(args)
	doc.flags.ignore_mandatory = 1
	doc.save()
