# -*- coding: utf-8 -*-
# Copyright (c) 2019, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import ast
from types import FunctionType, MethodType, ModuleType
from typing import Dict, List

import capkpi
from capkpi import _
from capkpi.model.document import Document
from capkpi.utils.safe_exec import NamespaceDict, get_safe_globals, safe_exec


class ServerScript(Document):
	def validate(self):
		capkpi.only_for("Script Manager", True)
		self.sync_scheduled_jobs()
		self.clear_scheduled_events()

	def on_update(self):
		capkpi.cache().delete_value("server_script_map")
		self.sync_scheduler_events()

	def on_trash(self):
		if self.script_type == "Scheduler Event":
			for job in self.scheduled_jobs:
				capkpi.delete_doc("Scheduled Job Type", job.name)

	@property
	def scheduled_jobs(self) -> List[Dict[str, str]]:
		return capkpi.get_all(
			"Scheduled Job Type",
			filters={"server_script": self.name},
			fields=["name", "stopped"],
		)

	def sync_scheduled_jobs(self):
		"""Sync Scheduled Job Type statuses if Server Script's disabled status is changed"""
		if self.script_type != "Scheduler Event" or not self.has_value_changed("disabled"):
			return

		for scheduled_job in self.scheduled_jobs:
			if bool(scheduled_job.stopped) != bool(self.disabled):
				job = capkpi.get_doc("Scheduled Job Type", scheduled_job.name)
				job.stopped = self.disabled
				job.save()

	def sync_scheduler_events(self):
		"""Create or update Scheduled Job Type documents for Scheduler Event Server Scripts"""
		if not self.disabled and self.event_frequency and self.script_type == "Scheduler Event":
			setup_scheduler_events(script_name=self.name, frequency=self.event_frequency)

	def clear_scheduled_events(self):
		"""Deletes existing scheduled jobs by Server Script if self.event_frequency has changed"""
		if self.script_type == "Scheduler Event" and self.has_value_changed("event_frequency"):
			for scheduled_job in self.scheduled_jobs:
				capkpi.delete_doc("Scheduled Job Type", scheduled_job.name)

	def execute_method(self) -> Dict:
		"""Specific to API endpoint Server Scripts

		Raises:
		        capkpi.DoesNotExistError: If self.script_type is not API
		        capkpi.PermissionError: If self.allow_guest is unset for API accessed by Guest user

		Returns:
		        dict: Evaluates self.script with capkpi.utils.safe_exec.safe_exec and returns the flags set in it's safe globals
		"""
		# wrong report type!
		if self.script_type != "API":
			raise capkpi.DoesNotExistError

		# validate if guest is allowed
		if capkpi.session.user == "Guest" and not self.allow_guest:
			raise capkpi.PermissionError

		# output can be stored in flags
		_globals, _locals = safe_exec(self.script)
		return _globals.capkpi.flags

	def execute_doc(self, doc: Document):
		"""Specific to Document Event triggered Server Scripts

		Args:
		        doc (Document): Executes script with for a certain document's events
		"""
		safe_exec(self.script, _locals={"doc": doc}, restrict_commit_rollback=True)

	def execute_scheduled_method(self):
		"""Specific to Scheduled Jobs via Server Scripts

		Raises:
		        capkpi.DoesNotExistError: If script type is not a scheduler event
		"""
		if self.script_type != "Scheduler Event":
			raise capkpi.DoesNotExistError

		safe_exec(self.script)

	def get_permission_query_conditions(self, user: str) -> List[str]:
		"""Specific to Permission Query Server Scripts

		Args:
		        user (str): Takes user email to execute script and return list of conditions

		Returns:
		        list: Returns list of conditions defined by rules in self.script
		"""
		locals = {"user": user, "conditions": ""}
		safe_exec(self.script, None, locals)
		if locals["conditions"]:
			return locals["conditions"]

	@capkpi.whitelist()
	def get_autocompletion_items(self):
		"""Generates a list of a autocompletion strings from the context dict
		that is used while executing a Server Script.

		Returns:
		        list: Returns list of autocompletion items.
		        For e.g., ["capkpi.utils.cint", "capkpi.db.get_all", ...]
		"""

		def get_keys(obj):
			out = []
			for key in obj:
				if key.startswith("_"):
					continue
				value = obj[key]
				if isinstance(value, (NamespaceDict, dict)) and value:
					if key == "form_dict":
						out.append(["form_dict", 7])
						continue
					for subkey, score in get_keys(value):
						fullkey = f"{key}.{subkey}"
						out.append([fullkey, score])
				else:
					if isinstance(value, type) and issubclass(value, Exception):
						score = 0
					elif isinstance(value, ModuleType):
						score = 10
					elif isinstance(value, (FunctionType, MethodType)):
						score = 9
					elif isinstance(value, type):
						score = 8
					elif isinstance(value, dict):
						score = 7
					else:
						score = 6
					out.append([key, score])
			return out

		items = capkpi.cache().get_value("server_script_autocompletion_items")
		if not items:
			items = get_keys(get_safe_globals())
			items = [{"value": d[0], "score": d[1]} for d in items]
			capkpi.cache().set_value("server_script_autocompletion_items", items)
		return items


@capkpi.whitelist()
def setup_scheduler_events(script_name, frequency):
	"""Creates or Updates Scheduled Job Type documents based on the specified script name and frequency

	Args:
	        script_name (str): Name of the Server Script document
	        frequency (str): Event label compatible with the CapKPI scheduler
	"""
	method = capkpi.scrub(f"{script_name}-{frequency}")
	scheduled_script = capkpi.db.get_value("Scheduled Job Type", {"method": method})

	if not scheduled_script:
		capkpi.get_doc(
			{
				"doctype": "Scheduled Job Type",
				"method": method,
				"frequency": frequency,
				"server_script": script_name,
			}
		).insert()

		capkpi.msgprint(_("Enabled scheduled execution for script {0}").format(script_name))

	else:
		doc = capkpi.get_doc("Scheduled Job Type", scheduled_script)

		if doc.frequency == frequency:
			return

		doc.frequency = frequency
		doc.save()

		capkpi.msgprint(_("Scheduled execution for script {0} has updated").format(script_name))