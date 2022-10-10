# -*- coding: utf-8 -*-
# Copyright (c) 2017, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi.model.document import Document


class PrintStyle(Document):
	def validate(self):
		if (
			self.standard == 1
			and not capkpi.local.conf.get("developer_mode")
			and not (capkpi.flags.in_import or capkpi.flags.in_test)
		):

			capkpi.throw(capkpi._("Standard Print Style cannot be changed. Please duplicate to edit."))

	def on_update(self):
		self.export_doc()

	def export_doc(self):
		# export
		from capkpi.modules.utils import export_module_json

		export_module_json(self, self.standard == 1, "Printing")
