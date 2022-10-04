# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi
import capkpi.www.list
from capkpi import _

no_cache = 1


def get_context(context):
	if capkpi.session.user == "Guest":
		capkpi.throw(_("You need to be logged in to access this page"), capkpi.PermissionError)

	context.show_sidebar = True
