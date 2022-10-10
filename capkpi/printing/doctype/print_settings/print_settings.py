# -*- coding: utf-8 -*-
# Copyright (c) 2018, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi import _
from capkpi.model.document import Document
from capkpi.utils import cint


class PrintSettings(Document):
	def validate(self):
		if self.pdf_page_size == "Custom" and not (self.pdf_page_height and self.pdf_page_width):
			capkpi.throw(_("Page height and width cannot be zero"))

	def on_update(self):
		capkpi.clear_cache()


@capkpi.whitelist()
def is_print_server_enabled():
	if not hasattr(capkpi.local, "enable_print_server"):
		capkpi.local.enable_print_server = cint(
			capkpi.db.get_single_value("Print Settings", "enable_print_server")
		)

	return capkpi.local.enable_print_server
