# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# See license.txt

from __future__ import unicode_literals

import capkpi


def get_context(context):
	token = capkpi.local.form_dict.token

	if token:
		capkpi.db.set_value("Integration Request", token, "status", "Cancelled")
		capkpi.db.commit()
