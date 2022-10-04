# Copyright (c) 2020, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi


def execute():
	capkpi.reload_doc("core", "doctype", "DocField")

	if capkpi.db.has_column("DocField", "show_days"):
		capkpi.db.sql(
			"""
			UPDATE
				tabDocField
			SET
				hide_days = 1 WHERE show_days = 0
		"""
		)
		capkpi.db.sql_ddl("alter table tabDocField drop column show_days")

	if capkpi.db.has_column("DocField", "show_seconds"):
		capkpi.db.sql(
			"""
			UPDATE
				tabDocField
			SET
				hide_seconds = 1 WHERE show_seconds = 0
		"""
		)
		capkpi.db.sql_ddl("alter table tabDocField drop column show_seconds")

	capkpi.clear_cache(doctype="DocField")
