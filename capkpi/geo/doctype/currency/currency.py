# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# License: See license.txt

from __future__ import unicode_literals

import capkpi
from capkpi import _, throw
from capkpi.model.document import Document


class Currency(Document):
	def validate(self):
		if not capkpi.flags.in_install_app:
			capkpi.clear_cache()
