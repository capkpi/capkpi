# -*- coding: utf-8 -*-
# Copyright (c) 2015, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi.model.document import Document


class CustomDocPerm(Document):
	def on_update(self):
		capkpi.clear_cache(doctype=self.parent)
