# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi

sitemap = 1


def get_context(context):
	context.doc = capkpi.get_doc("About Us Settings", "About Us Settings")

	return context
