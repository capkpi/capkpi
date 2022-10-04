# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import os
import unittest

import capkpi
import capkpi.translate

# class TestTranslations(unittest.TestCase):
# 	def test_doctype(self, messages=None):
# 		if not messages:
# 			messages = capkpi.translate.get_messages_from_doctype("Role")
# 		self.assertTrue("Role Name" in messages)
#
# 	def test_page(self, messages=None):
# 		if not messages:
# 			messages = capkpi.translate.get_messages_from_page("finder")
# 		self.assertTrue("Finder" in messages)
#
# 	def test_report(self, messages=None):
# 		if not messages:
# 			messages = capkpi.translate.get_messages_from_report("ToDo")
# 		self.assertTrue("Test" in messages)
#
# 	def test_include_js(self, messages=None):
# 		if not messages:
# 			messages = capkpi.translate.get_messages_from_include_files("capkpi")
# 		self.assertTrue("History" in messages)
#
# 	def test_server(self, messages=None):
# 		if not messages:
# 			messages = capkpi.translate.get_server_messages("capkpi")
# 		self.assertTrue("Login" in messages)
# 		self.assertTrue("Did not save" in messages)
#
# 	def test_all_app(self):
# 		messages = capkpi.translate.get_messages_for_app("capkpi")
# 		self.test_doctype(messages)
# 		self.test_page(messages)
# 		self.test_report(messages)
# 		self.test_include_js(messages)
# 		self.test_server(messages)
#
# 	def test_load_translations(self):
# 		capkpi.translate.clear_cache()
# 		self.assertFalse(capkpi.cache().hget("lang_full_dict", "de"))
#
# 		langdict = capkpi.translate.get_full_dict("de")
# 		self.assertEqual(langdict['Row'], 'Reihe')
#
# 	def test_write_csv(self):
# 		tpath = capkpi.get_pymodule_path("capkpi", "translations", "de.csv")
# 		if os.path.exists(tpath):
# 			os.remove(tpath)
# 		capkpi.translate.write_translations_file("capkpi", "de")
# 		self.assertTrue(os.path.exists(tpath))
# 		self.assertEqual(dict(capkpi.translate.read_csv_file(tpath)).get("Row"), "Reihe")
#
# 	def test_get_dict(self):
# 		capkpi.local.lang = "de"
# 		self.assertEqual(capkpi.get_lang_dict("doctype", "Role").get("Role"), "Rolle")
# 		capkpi.local.lang = "en"
#
# if __name__=="__main__":
# 	capkpi.connect("site1")
# 	unittest.main()
