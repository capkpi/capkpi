# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import print_function, unicode_literals

import capkpi

no_cache = 1


def get_context(context):
	if capkpi.flags.in_migrate:
		return
	context.http_status_code = 500
	print(capkpi.get_traceback())
	return {"error": capkpi.get_traceback().replace("<", "&lt;").replace(">", "&gt;")}
