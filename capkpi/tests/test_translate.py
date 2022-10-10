# Copyright (c) 2021, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import os
import unittest
from random import choices
from unittest.mock import patch

import capkpi
import capkpi.translate
from capkpi import _
from capkpi.translate import get_language, get_parent_language, get_translation_dict_from_file
from capkpi.utils import set_request

dirname = os.path.dirname(__file__)
translation_string_file = os.path.join(dirname, "translation_test_file.txt")
first_lang, second_lang, third_lang, fourth_lang, fifth_lang = choices(
	# skip "en*" since it is a default language
	capkpi.get_all("Language", pluck="name", filters=[["name", "not like", "en%"]]),
	k=5,
)


class TestTranslate(unittest.TestCase):
	guest_sessions_required = [
		"test_guest_request_language_resolution_with_cookie",
		"test_guest_request_language_resolution_with_request_header",
	]

	def setUp(self):
		if self._testMethodName in self.guest_sessions_required:
			capkpi.set_user("Guest")
		capkpi.local.lang_full_dict = None  # reset cached translations

	def tearDown(self):
		capkpi.form_dict.pop("_lang", None)
		if self._testMethodName in self.guest_sessions_required:
			capkpi.set_user("Administrator")
		capkpi.local.lang_full_dict = None  # reset cached translations

	def test_extract_message_from_file(self):
		data = capkpi.translate.get_messages_from_file(translation_string_file)
		exp_filename = "apps/capkpi/capkpi/tests/translation_test_file.txt"

		self.assertEqual(
			len(data),
			len(expected_output),
			msg=f"Mismatched output:\nExpected: {expected_output}\nFound: {data}",
		)

		for extracted, expected in zip(data, expected_output):
			ext_filename, ext_message, ext_context, ext_line = extracted
			exp_message, exp_context, exp_line = expected
			self.assertEqual(ext_filename, exp_filename)
			self.assertEqual(ext_message, exp_message)
			self.assertEqual(ext_context, exp_context)
			self.assertEqual(ext_line, exp_line)

	def test_translation_with_context(self):
		try:
			capkpi.local.lang = "fr"
			self.assertEqual(_("Change"), "Changement")
			self.assertEqual(_("Change", context="Coins"), "la monnaie")
		finally:
			capkpi.local.lang = "en"

	def test_request_language_resolution_with_form_dict(self):
		"""Test for capkpi.translate.get_language

		Case 1: capkpi.form_dict._lang is set
		"""

		capkpi.form_dict._lang = first_lang

		with patch.object(capkpi.translate, "get_preferred_language_cookie", return_value=second_lang):
			return_val = get_language()

		self.assertIn(return_val, [first_lang, get_parent_language(first_lang)])

	def test_request_language_resolution_with_cookie(self):
		"""Test for capkpi.translate.get_language

		Case 2: capkpi.form_dict._lang is not set, but preferred_language cookie is
		"""

		with patch.object(capkpi.translate, "get_preferred_language_cookie", return_value="fr"):
			set_request(method="POST", path="/", headers=[("Accept-Language", "hr")])
			return_val = get_language()
			# system default language
			self.assertEqual(return_val, "en")
			self.assertNotIn(return_val, [second_lang, get_parent_language(second_lang)])

	def test_guest_request_language_resolution_with_cookie(self):
		"""Test for capkpi.translate.get_language

		Case 3: capkpi.form_dict._lang is not set, but preferred_language cookie is [Guest User]
		"""

		with patch.object(capkpi.translate, "get_preferred_language_cookie", return_value=second_lang):
			set_request(method="POST", path="/", headers=[("Accept-Language", third_lang)])
			return_val = get_language()

		self.assertIn(return_val, [second_lang, get_parent_language(second_lang)])

	def test_guest_request_language_resolution_with_request_header(self):
		"""Test for capkpi.translate.get_language

		Case 4: capkpi.form_dict._lang & preferred_language cookie is not set, but Accept-Language header is [Guest User]
		"""

		set_request(method="POST", path="/", headers=[("Accept-Language", third_lang)])
		return_val = get_language()
		self.assertIn(return_val, [third_lang, get_parent_language(third_lang)])

	def test_request_language_resolution_with_request_header(self):
		"""Test for capkpi.translate.get_language

		Case 5: capkpi.form_dict._lang & preferred_language cookie is not set, but Accept-Language header is
		"""

		set_request(method="POST", path="/", headers=[("Accept-Language", third_lang)])
		return_val = get_language()
		self.assertNotIn(return_val, [third_lang, get_parent_language(third_lang)])

	def test_load_all_translate_files(self):
		"""Load all CSV files to ensure they have correct format"""
		verify_translation_files("capkpi")


def verify_translation_files(app):
	"""Function to verify translation file syntax in app."""
	# Do not remove/rename this, other apps depend on it to test their translations

	from pathlib import Path

	translations_dir = Path(capkpi.get_app_path(app)) / "translations"

	for file in translations_dir.glob("*.csv"):
		lang = file.stem  # basename of file = lang
		get_translation_dict_from_file(file, lang, app, throw=True)


expected_output = [
	("Warning: Unable to find {0} in any table related to {1}", "This is some context", 2),
	("Warning: Unable to find {0} in any table related to {1}", None, 4),
	("You don't have any messages yet.", None, 6),
	("Submit", "Some DocType", 8),
	("Warning: Unable to find {0} in any table related to {1}", "This is some context", 15),
	("Submit", "Some DocType", 17),
	("You don't have any messages yet.", None, 19),
	("You don't have any messages yet.", None, 21),
	("Long string that needs its own line because of black formatting.", None, 24),
	("Long string with", "context", 28),
	("Long string with", "context on newline", 32),
]