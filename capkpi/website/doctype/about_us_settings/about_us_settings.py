# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi.model.document import Document


class AboutUsSettings(Document):
	def on_update(self):
		from capkpi.website.render import clear_cache

		clear_cache("about")


def get_args():
	obj = capkpi.get_doc("About Us Settings")
	return {"obj": obj}
