# Copyright (c) 2020, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi


def execute():
	if capkpi.db.exists("DocType", "Event Producer"):
		capkpi.db.sql("""UPDATE `tabEvent Producer` SET api_key='', api_secret=''""")
	if capkpi.db.exists("DocType", "Event Consumer"):
		capkpi.db.sql("""UPDATE `tabEvent Consumer` SET api_key='', api_secret=''""")
