# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import capkpi
from capkpi import _
from capkpi.model.document import Document


class ClientScript(Document):
	def autoname(self):
		self.name = f"{self.dt}-{self.view}"

	def validate(self):
		if not self.is_new():
			return

		exists = capkpi.db.exists("Client Script", {"dt": self.dt, "view": self.view})
		if exists:
			capkpi.throw(
				_("Client Script for {0} {1} already exists").format(capkpi.bold(self.dt), self.view),
				capkpi.DuplicateEntryError,
			)

	def on_update(self):
		capkpi.clear_cache(doctype=self.dt)

	def on_trash(self):
		capkpi.clear_cache(doctype=self.dt)
