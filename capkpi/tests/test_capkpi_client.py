# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import base64
import unittest

import requests

import capkpi
from capkpi.core.doctype.user.user import generate_keys
from capkpi.capkpiclient import CapKPIClient, CapKPIException
from capkpi.utils.data import get_url


class TestCapKPIClient(unittest.TestCase):
	def test_insert_many(self):
		server = CapKPIClient(get_url(), "Administrator", "admin", verify=False)
		capkpi.db.sql("delete from `tabNote` where title in ('Sing','a','song','of','sixpence')")
		capkpi.db.commit()

		server.insert_many(
			[
				{"doctype": "Note", "public": True, "title": "Sing"},
				{"doctype": "Note", "public": True, "title": "a"},
				{"doctype": "Note", "public": True, "title": "song"},
				{"doctype": "Note", "public": True, "title": "of"},
				{"doctype": "Note", "public": True, "title": "sixpence"},
			]
		)

		self.assertTrue(capkpi.db.get_value("Note", {"title": "Sing"}))
		self.assertTrue(capkpi.db.get_value("Note", {"title": "a"}))
		self.assertTrue(capkpi.db.get_value("Note", {"title": "song"}))
		self.assertTrue(capkpi.db.get_value("Note", {"title": "of"}))
		self.assertTrue(capkpi.db.get_value("Note", {"title": "sixpence"}))

	def test_create_doc(self):
		server = CapKPIClient(get_url(), "Administrator", "admin", verify=False)
		capkpi.db.sql("delete from `tabNote` where title = 'test_create'")
		capkpi.db.commit()

		server.insert({"doctype": "Note", "public": True, "title": "test_create"})

		self.assertTrue(capkpi.db.get_value("Note", {"title": "test_create"}))

	def test_list_docs(self):
		server = CapKPIClient(get_url(), "Administrator", "admin", verify=False)
		doc_list = server.get_list("Note")

		self.assertTrue(len(doc_list))

	def test_get_doc(self):
		server = CapKPIClient(get_url(), "Administrator", "admin", verify=False)
		capkpi.db.sql("delete from `tabNote` where title = 'get_this'")
		capkpi.db.commit()

		server.insert_many(
			[
				{"doctype": "Note", "public": True, "title": "get_this"},
			]
		)
		doc = server.get_doc("Note", "get_this")
		self.assertTrue(doc)

	def test_get_value(self):
		server = CapKPIClient(get_url(), "Administrator", "admin", verify=False)
		capkpi.db.sql("delete from `tabNote` where title = 'get_value'")
		capkpi.db.commit()

		test_content = "test get value"

		server.insert_many(
			[
				{"doctype": "Note", "public": True, "title": "get_value", "content": test_content},
			]
		)
		self.assertEqual(
			server.get_value("Note", "content", {"title": "get_value"}).get("content"), test_content
		)
		name = server.get_value("Note", "name", {"title": "get_value"}).get("name")

		# test by name
		self.assertEqual(server.get_value("Note", "content", name).get("content"), test_content)

		self.assertRaises(
			CapKPIException,
			server.get_value,
			"Note",
			"(select (password) from(__Auth) order by name desc limit 1)",
			{"title": "get_value"},
		)

	def test_get_single(self):
		server = CapKPIClient(get_url(), "Administrator", "admin", verify=False)
		server.set_value("Website Settings", "Website Settings", "title_prefix", "test-prefix")
		self.assertEqual(
			server.get_value("Website Settings", "title_prefix", "Website Settings").get("title_prefix"),
			"test-prefix",
		)
		self.assertEqual(
			server.get_value("Website Settings", "title_prefix").get("title_prefix"), "test-prefix"
		)
		capkpi.db.set_value("Website Settings", None, "title_prefix", "")

	def test_update_doc(self):
		server = CapKPIClient(get_url(), "Administrator", "admin", verify=False)
		capkpi.db.sql("delete from `tabNote` where title in ('Sing','sing')")
		capkpi.db.commit()

		server.insert({"doctype": "Note", "public": True, "title": "Sing"})
		doc = server.get_doc("Note", "Sing")
		changed_title = "sing"
		doc["title"] = changed_title
		doc = server.update(doc)
		self.assertTrue(doc["title"] == changed_title)

	def test_update_child_doc(self):
		server = CapKPIClient(get_url(), "Administrator", "admin", verify=False)
		capkpi.db.sql("delete from `tabContact` where first_name = 'George' and last_name = 'Steevens'")
		capkpi.db.sql(
			"delete from `tabContact` where first_name = 'William' and last_name = 'Shakespeare'"
		)
		capkpi.db.sql("delete from `tabCommunication` where reference_doctype = 'Event'")
		capkpi.db.sql("delete from `tabCommunication Link` where link_doctype = 'Contact'")
		capkpi.db.sql("delete from `tabEvent` where subject = 'Sing a song of sixpence'")
		capkpi.db.sql("delete from `tabEvent Participants` where reference_doctype = 'Contact'")
		capkpi.db.commit()

		# create multiple contacts
		server.insert_many(
			[
				{"doctype": "Contact", "first_name": "George", "last_name": "Steevens"},
				{"doctype": "Contact", "first_name": "William", "last_name": "Shakespeare"},
			]
		)

		# create an event with one of the created contacts
		event = server.insert(
			{
				"doctype": "Event",
				"subject": "Sing a song of sixpence",
				"event_participants": [
					{"reference_doctype": "Contact", "reference_docname": "George Steevens"}
				],
			}
		)

		# update the event's contact to the second contact
		server.update(
			{
				"doctype": "Event Participants",
				"name": event.get("event_participants")[0].get("name"),
				"reference_docname": "William Shakespeare",
			}
		)

		# the change should run the parent document's validations and
		# create a Communication record with the new contact
		self.assertTrue(capkpi.db.exists("Communication Link", {"link_name": "William Shakespeare"}))

	def test_delete_doc(self):
		server = CapKPIClient(get_url(), "Administrator", "admin", verify=False)
		capkpi.db.sql("delete from `tabNote` where title = 'delete'")
		capkpi.db.commit()

		server.insert_many(
			[
				{"doctype": "Note", "public": True, "title": "delete"},
			]
		)
		server.delete("Note", "delete")

		self.assertFalse(capkpi.db.get_value("Note", {"title": "delete"}))

	def test_auth_via_api_key_secret(self):
		# generate API key and API secret for administrator
		keys = generate_keys("Administrator")
		capkpi.db.commit()
		generated_secret = capkpi.utils.password.get_decrypted_password(
			"User", "Administrator", fieldname="api_secret"
		)

		api_key = capkpi.db.get_value("User", "Administrator", "api_key")
		header = {"Authorization": "token {}:{}".format(api_key, generated_secret)}
		res = requests.post(get_url() + "/api/method/capkpi.auth.get_logged_user", headers=header)

		self.assertEqual(res.status_code, 200)
		self.assertEqual("Administrator", res.json()["message"])
		self.assertEqual(keys["api_secret"], generated_secret)

		header = {
			"Authorization": "Basic {}".format(
				base64.b64encode(capkpi.safe_encode("{}:{}".format(api_key, generated_secret))).decode()
			)
		}
		res = requests.post(get_url() + "/api/method/capkpi.auth.get_logged_user", headers=header)
		self.assertEqual(res.status_code, 200)
		self.assertEqual("Administrator", res.json()["message"])

		# Valid api key, invalid api secret
		api_secret = "ksk&93nxoe3os"
		header = {"Authorization": "token {}:{}".format(api_key, api_secret)}
		res = requests.post(get_url() + "/api/method/capkpi.auth.get_logged_user", headers=header)
		self.assertEqual(res.status_code, 403)

		# random api key and api secret
		api_key = "@3djdk3kld"
		api_secret = "ksk&93nxoe3os"
		header = {"Authorization": "token {}:{}".format(api_key, api_secret)}
		res = requests.post(get_url() + "/api/method/capkpi.auth.get_logged_user", headers=header)
		self.assertEqual(res.status_code, 401)
