# -*- coding: utf-8 -*-
# Copyright (c) 2019, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json
import os

import requests

import capkpi
from capkpi import _
from capkpi.capkpiclient import CapKPIClient
from capkpi.model.document import Document
from capkpi.utils.background_jobs import get_jobs
from capkpi.utils.data import get_url


class EventConsumer(Document):
	def validate(self):
		# approve subscribed doctypes for tests
		# capkpi.flags.in_test won't work here as tests are running on the consumer site
		if os.environ.get("CI"):
			for entry in self.consumer_doctypes:
				entry.status = "Approved"

	def on_update(self):
		if not self.incoming_change:
			doc_before_save = self.get_doc_before_save()
			if doc_before_save.api_key != self.api_key or doc_before_save.api_secret != self.api_secret:
				return

			self.update_consumer_status()
		else:
			capkpi.db.set_value(self.doctype, self.name, "incoming_change", 0)

		capkpi.cache().delete_value("event_consumer_document_type_map")

	def on_trash(self):
		for i in capkpi.get_all("Event Update Log Consumer", {"consumer": self.name}):
			capkpi.delete_doc("Event Update Log Consumer", i.name)
		capkpi.cache().delete_value("event_consumer_document_type_map")

	def update_consumer_status(self):
		consumer_site = get_consumer_site(self.callback_url)
		event_producer = consumer_site.get_doc("Event Producer", get_url())
		event_producer = capkpi._dict(event_producer)
		config = event_producer.producer_doctypes
		event_producer.producer_doctypes = []
		for entry in config:
			if entry.get("has_mapping"):
				ref_doctype = consumer_site.get_value(
					"Document Type Mapping", "remote_doctype", entry.get("mapping")
				).get("remote_doctype")
			else:
				ref_doctype = entry.get("ref_doctype")

			entry["status"] = capkpi.db.get_value(
				"Event Consumer Document Type", {"parent": self.name, "ref_doctype": ref_doctype}, "status"
			)

		event_producer.producer_doctypes = config
		# when producer doc is updated it updates the consumer doc
		# set flag to avoid deadlock
		event_producer.incoming_change = True
		consumer_site.update(event_producer)

	def get_consumer_status(self):
		response = requests.get(self.callback_url)
		if response.status_code != 200:
			return "offline"
		return "online"


@capkpi.whitelist()
def register_consumer(data):
	"""create an event consumer document for registering a consumer"""
	data = json.loads(data)
	# to ensure that consumer is created only once
	if capkpi.db.exists("Event Consumer", data["event_consumer"]):
		return None

	user = data["user"]
	if not capkpi.db.exists("User", user):
		capkpi.throw(_("User {0} not found on the producer site").format(user))

	if "System Manager" not in capkpi.get_roles(user):
		capkpi.throw(_("Event Subscriber has to be a System Manager."))

	consumer = capkpi.new_doc("Event Consumer")
	consumer.callback_url = data["event_consumer"]
	consumer.user = data["user"]
	consumer.api_key = data["api_key"]
	consumer.api_secret = data["api_secret"]
	consumer.incoming_change = True
	consumer_doctypes = json.loads(data["consumer_doctypes"])

	for entry in consumer_doctypes:
		consumer.append(
			"consumer_doctypes",
			{"ref_doctype": entry.get("doctype"), "status": "Pending", "condition": entry.get("condition")},
		)

	consumer.insert()

	# consumer's 'last_update' field should point to the latest update
	# in producer's update log when subscribing
	# so that, updates after subscribing are consumed and not the old ones.
	last_update = str(get_last_update())
	return json.dumps({"last_update": last_update})


def get_consumer_site(consumer_url):
	"""create a CapKPIClient object for event consumer site"""
	consumer_doc = capkpi.get_doc("Event Consumer", consumer_url)
	consumer_site = CapKPIClient(
		url=consumer_url,
		api_key=consumer_doc.api_key,
		api_secret=consumer_doc.get_password("api_secret"),
	)
	return consumer_site


def get_last_update():
	"""get the creation timestamp of last update consumed"""
	updates = capkpi.get_list(
		"Event Update Log", "creation", ignore_permissions=True, limit=1, order_by="creation desc"
	)
	if updates:
		return updates[0].creation
	return capkpi.utils.now_datetime()


@capkpi.whitelist()
def notify_event_consumers(doctype):
	"""get all event consumers and set flag for notification status"""
	event_consumers = capkpi.get_all(
		"Event Consumer Document Type", ["parent"], {"ref_doctype": doctype, "status": "Approved"}
	)
	for entry in event_consumers:
		consumer = capkpi.get_doc("Event Consumer", entry.parent)
		consumer.flags.notified = False
		notify(consumer)


@capkpi.whitelist()
def notify(consumer):
	"""notify individual event consumers about a new update"""
	consumer_status = consumer.get_consumer_status()
	if consumer_status == "online":
		try:
			client = get_consumer_site(consumer.callback_url)
			client.post_request(
				{
					"cmd": "capkpi.event_streaming.doctype.event_producer.event_producer.new_event_notification",
					"producer_url": get_url(),
				}
			)
			consumer.flags.notified = True
		except Exception:
			consumer.flags.notified = False
	else:
		consumer.flags.notified = False

	# enqueue another job if the site was not notified
	if not consumer.flags.notified:
		enqueued_method = "capkpi.event_streaming.doctype.event_consumer.event_consumer.notify"
		jobs = get_jobs()
		if not jobs or enqueued_method not in jobs[capkpi.local.site] and not consumer.flags.notifed:
			capkpi.enqueue(
				enqueued_method, queue="long", enqueue_after_commit=True, **{"consumer": consumer}
			)


def has_consumer_access(consumer, update_log):
	"""Checks if consumer has completely satisfied all the conditions on the doc"""

	if isinstance(consumer, str):
		consumer = capkpi.get_doc("Event Consumer", consumer)

	if not capkpi.db.exists(update_log.ref_doctype, update_log.docname):
		# Delete Log
		# Check if the last Update Log of this document was read by this consumer
		last_update_log = capkpi.get_all(
			"Event Update Log",
			filters={
				"ref_doctype": update_log.ref_doctype,
				"docname": update_log.docname,
				"creation": ["<", update_log.creation],
			},
			order_by="creation desc",
			limit_page_length=1,
		)
		if not len(last_update_log):
			return False

		last_update_log = capkpi.get_doc("Event Update Log", last_update_log[0].name)
		return len([x for x in last_update_log.consumers if x.consumer == consumer.name])

	doc = capkpi.get_doc(update_log.ref_doctype, update_log.docname)
	try:
		for dt_entry in consumer.consumer_doctypes:
			if dt_entry.ref_doctype != update_log.ref_doctype:
				continue

			if not dt_entry.condition:
				return True

			condition: str = dt_entry.condition
			if condition.startswith("cmd:"):
				cmd = condition.split("cmd:")[1].strip()
				args = {"consumer": consumer, "doc": doc, "update_log": update_log}
				return capkpi.call(cmd, **args)
			else:
				return capkpi.safe_eval(condition, capkpi._dict(doc=doc))
	except Exception as e:
		capkpi.log_error(title="has_consumer_access error", message=e)
	return False
