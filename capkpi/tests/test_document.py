# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import unittest
from unittest.mock import Mock

import capkpi
from capkpi.model.naming import make_autoname, parse_naming_series, revert_series_if_last
from capkpi.utils import cint, set_request
from capkpi.website import render

from . import update_system_settings


class TestDocument(unittest.TestCase):
	def test_get_return_empty_list_for_table_field_if_none(self):
		d = capkpi.get_doc({"doctype": "User"})
		self.assertEqual(d.get("roles"), [])

	def test_load(self):
		d = capkpi.get_doc("DocType", "User")
		self.assertEqual(d.doctype, "DocType")
		self.assertEqual(d.name, "User")
		self.assertEqual(d.allow_rename, 1)
		self.assertTrue(isinstance(d.fields, list))
		self.assertTrue(isinstance(d.permissions, list))
		self.assertTrue(filter(lambda d: d.fieldname == "email", d.fields))

	def test_load_single(self):
		d = capkpi.get_doc("Website Settings", "Website Settings")
		self.assertEqual(d.name, "Website Settings")
		self.assertEqual(d.doctype, "Website Settings")
		self.assertTrue(d.disable_signup in (0, 1))

	def test_insert(self):
		d = capkpi.get_doc(
			{
				"doctype": "Event",
				"subject": "test-doc-test-event 1",
				"starts_on": "2014-01-01",
				"event_type": "Public",
			}
		)
		d.insert()
		self.assertTrue(d.name.startswith("EV"))
		self.assertEqual(capkpi.db.get_value("Event", d.name, "subject"), "test-doc-test-event 1")

		# test if default values are added
		self.assertEqual(d.send_reminder, 1)
		return d

	def test_insert_with_child(self):
		d = capkpi.get_doc(
			{
				"doctype": "Event",
				"subject": "test-doc-test-event 2",
				"starts_on": "2014-01-01",
				"event_type": "Public",
			}
		)
		d.insert()
		self.assertTrue(d.name.startswith("EV"))
		self.assertEqual(capkpi.db.get_value("Event", d.name, "subject"), "test-doc-test-event 2")

	def test_update(self):
		d = self.test_insert()
		d.subject = "subject changed"
		d.save()

		self.assertEqual(capkpi.db.get_value(d.doctype, d.name, "subject"), "subject changed")

	def test_value_changed(self):
		d = self.test_insert()
		d.subject = "subject changed again"
		d.save()
		self.assertTrue(d.has_value_changed("subject"))
		self.assertFalse(d.has_value_changed("event_type"))

	def test_mandatory(self):
		# TODO: recheck if it is OK to force delete
		capkpi.delete_doc_if_exists("User", "test_mandatory@example.com", 1)

		d = capkpi.get_doc(
			{
				"doctype": "User",
				"email": "test_mandatory@example.com",
			}
		)
		self.assertRaises(capkpi.MandatoryError, d.insert)

		d.set("first_name", "Test Mandatory")
		d.insert()
		self.assertEqual(capkpi.db.get_value("User", d.name), d.name)

	def test_conflict_validation(self):
		d1 = self.test_insert()
		d2 = capkpi.get_doc(d1.doctype, d1.name)
		d1.save()
		self.assertRaises(capkpi.TimestampMismatchError, d2.save)

	def test_conflict_validation_single(self):
		d1 = capkpi.get_doc("Website Settings", "Website Settings")
		d1.home_page = "test-web-page-1"

		d2 = capkpi.get_doc("Website Settings", "Website Settings")
		d2.home_page = "test-web-page-1"

		d1.save()
		self.assertRaises(capkpi.TimestampMismatchError, d2.save)

	def test_permission(self):
		capkpi.set_user("Guest")
		self.assertRaises(capkpi.PermissionError, self.test_insert)
		capkpi.set_user("Administrator")

	def test_permission_single(self):
		capkpi.set_user("Guest")
		d = capkpi.get_doc("Website Settings", "Website Settings")
		self.assertRaises(capkpi.PermissionError, d.save)
		capkpi.set_user("Administrator")

	def test_link_validation(self):
		capkpi.delete_doc_if_exists("User", "test_link_validation@example.com", 1)

		d = capkpi.get_doc(
			{
				"doctype": "User",
				"email": "test_link_validation@example.com",
				"first_name": "Link Validation",
				"roles": [{"role": "ABC"}],
			}
		)
		self.assertRaises(capkpi.LinkValidationError, d.insert)

		d.roles = []
		d.append("roles", {"role": "System Manager"})
		d.insert()

		self.assertEqual(capkpi.db.get_value("User", d.name), d.name)

	def test_validate(self):
		d = self.test_insert()
		d.starts_on = "2014-01-01"
		d.ends_on = "2013-01-01"
		self.assertRaises(capkpi.ValidationError, d.validate)
		self.assertRaises(capkpi.ValidationError, d.run_method, "validate")
		self.assertRaises(capkpi.ValidationError, d.save)

	def test_update_after_submit(self):
		d = self.test_insert()
		d.starts_on = "2014-09-09"
		self.assertRaises(capkpi.UpdateAfterSubmitError, d.validate_update_after_submit)
		d.meta.get_field("starts_on").allow_on_submit = 1
		d.validate_update_after_submit()
		d.meta.get_field("starts_on").allow_on_submit = 0

		# when comparing date(2014, 1, 1) and "2014-01-01"
		d.reload()
		d.starts_on = "2014-01-01"
		d.validate_update_after_submit()

	def test_varchar_length(self):
		d = self.test_insert()
		d.sender = "abcde" * 100 + "@user.com"
		self.assertRaises(capkpi.CharacterLengthExceededError, d.save)

	def test_xss_filter(self):
		d = self.test_insert()

		# script
		xss = '<script>alert("XSS")</script>'
		escaped_xss = xss.replace("<", "&lt;").replace(">", "&gt;")
		d.subject += xss
		d.save()
		d.reload()

		self.assertTrue(xss not in d.subject)
		self.assertTrue(escaped_xss in d.subject)

		# onload
		xss = '<div onload="alert("XSS")">Test</div>'
		escaped_xss = "<div>Test</div>"
		d.subject += xss
		d.save()
		d.reload()

		self.assertTrue(xss not in d.subject)
		self.assertTrue(escaped_xss in d.subject)

		# css attributes
		xss = '<div style="something: doesn\'t work; color: red;">Test</div>'
		escaped_xss = '<div style="">Test</div>'
		d.subject += xss
		d.save()
		d.reload()

		self.assertTrue(xss not in d.subject)
		self.assertTrue(escaped_xss in d.subject)

	def test_naming_series(self):
		data = ["TEST-", "TEST/17-18/.test_data./.####", "TEST.YYYY.MM.####"]

		for series in data:
			name = make_autoname(series)
			prefix = series

			if ".#" in series:
				prefix = series.rsplit(".", 1)[0]

			prefix = parse_naming_series(prefix)
			old_current = capkpi.db.get_value("Series", prefix, "current", order_by="name")

			revert_series_if_last(series, name)
			new_current = cint(capkpi.db.get_value("Series", prefix, "current", order_by="name"))

			self.assertEqual(cint(old_current) - 1, new_current)

	def test_non_negative_check(self):
		capkpi.delete_doc_if_exists("Currency", "CapKPI Coin", 1)

		d = capkpi.get_doc(
			{"doctype": "Currency", "currency_name": "CapKPI Coin", "smallest_currency_fraction_value": -1}
		)

		self.assertRaises(capkpi.NonNegativeError, d.insert)

		d.set("smallest_currency_fraction_value", 1)
		d.insert()
		self.assertEqual(capkpi.db.get_value("Currency", d.name), d.name)

		capkpi.delete_doc_if_exists("Currency", "CapKPI Coin", 1)

	def test_get_formatted(self):
		capkpi.get_doc(
			{
				"doctype": "DocType",
				"name": "Test Formatted",
				"module": "Custom",
				"custom": 1,
				"fields": [
					{"label": "Currency", "fieldname": "currency", "reqd": 1, "fieldtype": "Currency"},
				],
			}
		).insert()

		capkpi.delete_doc_if_exists("Currency", "INR", 1)

		d = capkpi.get_doc(
			{
				"doctype": "Currency",
				"currency_name": "INR",
				"symbol": "₹",
			}
		).insert()

		d = capkpi.get_doc({"doctype": "Test Formatted", "currency": 100000})
		self.assertEquals(d.get_formatted("currency", currency="INR", format="#,###.##"), "₹ 100,000.00")

	def test_limit_for_get(self):
		doc = capkpi.get_doc("DocType", "DocType")
		# assuming DocType has more than 3 Data fields
		self.assertEquals(len(doc.get("fields", limit=3)), 3)

		# limit with filters
		self.assertEquals(len(doc.get("fields", filters={"fieldtype": "Data"}, limit=3)), 3)

	def test_run_method(self):
		doc = capkpi.get_last_doc("User")

		# Case 1: Override with a string
		doc.as_dict = ""

		# run_method should throw TypeError
		self.assertRaisesRegex(TypeError, "not callable", doc.run_method, "as_dict")

		# Case 2: Override with a function
		def my_as_dict(*args, **kwargs):
			return "success"

		doc.as_dict = my_as_dict

		# run_method should get overridden
		self.assertEqual(doc.run_method("as_dict"), "success")

	def test_realtime_notify(self):
		todo = capkpi.new_doc("ToDo")
		todo.description = "this will trigger realtime update"
		todo.notify_update = Mock()
		todo.insert()
		self.assertEqual(todo.notify_update.call_count, 1)

		todo.reload()
		todo.flags.notify_update = False
		todo.description = "this won't trigger realtime update"
		todo.save()
		self.assertEqual(todo.notify_update.call_count, 1)


class TestDocumentWebView(unittest.TestCase):
	def get(self, path):
		from capkpi.app import make_form_dict

		capkpi.set_user("Guest")
		set_request(method="GET", path=path)
		make_form_dict(capkpi.local.request)
		response = render.render()
		capkpi.set_user("Administrator")
		return response

	def test_web_view_link_authentication(self):
		todo = capkpi.get_doc({"doctype": "ToDo", "description": "Test"}).insert()
		document_key = todo.get_document_share_key()
		capkpi.db.commit()

		# with old-style signature key
		update_system_settings({"allow_older_web_view_links": True}, True)
		old_document_key = todo.get_signature()
		url = f"/ToDo/{todo.name}?key={old_document_key}"
		self.assertEquals(self.get(url).status, "200 OK")

		update_system_settings({"allow_older_web_view_links": False}, True)
		self.assertEquals(self.get(url).status, "401 UNAUTHORIZED")

		# with valid key
		url = f"/ToDo/{todo.name}?key={document_key}"
		self.assertEquals(self.get(url).status, "200 OK")

		# with invalid key
		invalid_key_url = f"/ToDo/{todo.name}?key=INVALID_KEY"
		self.assertEquals(self.get(invalid_key_url).status, "401 UNAUTHORIZED")

		# expire the key
		document_key_doc = capkpi.get_doc("Document Share Key", {"key": document_key})
		document_key_doc.expires_on = "2020-01-01"
		document_key_doc.save(ignore_permissions=True)
		capkpi.db.commit()

		# with expired key
		self.assertEquals(self.get(url).status, "410 GONE")

		# without key
		url_without_key = f"/ToDo/{todo.name}"
		self.assertEquals(self.get(url_without_key).status, "403 FORBIDDEN")
