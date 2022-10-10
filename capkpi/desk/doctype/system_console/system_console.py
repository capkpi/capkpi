# -*- coding: utf-8 -*-
# Copyright (c) 2020, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json

import capkpi
from capkpi.model.document import Document
from capkpi.utils.safe_exec import safe_exec


class SystemConsole(Document):
	def run(self):
		capkpi.only_for("System Manager")
		try:
			capkpi.debug_log = []
			safe_exec(self.console)
			self.output = "\n".join(capkpi.debug_log)
		except Exception:
			self.output = capkpi.get_traceback()

		if self.commit:
			capkpi.db.commit()
		else:
			capkpi.db.rollback()

		capkpi.get_doc(dict(doctype="Console Log", script=self.console, output=self.output)).insert()
		capkpi.db.commit()


@capkpi.whitelist()
def execute_code(doc):
	console = capkpi.get_doc(json.loads(doc))
	console.run()
	return console.as_dict()
