# -*- coding: utf-8 -*-
# Copyright (c) 2020, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from capkpi.desk.utils import slug
from capkpi.model.document import Document


class DocTypeLayout(Document):
	def validate(self):
		if not self.route:
			self.route = slug(self.name)
