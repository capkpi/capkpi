# Copyright (c) 2020, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi


def execute():
	"""Enable all the existing Client script"""

	capkpi.db.sql(
		"""
		UPDATE `tabClient Script` SET enabled=1
	"""
	)
