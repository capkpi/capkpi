# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi.model.document import Document


class WebsiteScript(Document):
	def on_update(self):
		"""clear cache"""
		capkpi.clear_cache(user="Guest")

		from capkpi.website.render import clear_cache

		clear_cache()
