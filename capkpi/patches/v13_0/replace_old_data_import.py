# Copyright (c) 2020, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi


def execute():
	if not capkpi.db.table_exists("Data Import"):
		return

	meta = capkpi.get_meta("Data Import")
	# if Data Import is the new one, return early
	if meta.fields[1].fieldname == "import_type":
		return

	capkpi.db.sql("DROP TABLE IF EXISTS `tabData Import Legacy`")
	capkpi.rename_doc("DocType", "Data Import", "Data Import Legacy")
	capkpi.db.commit()
	capkpi.db.sql("DROP TABLE IF EXISTS `tabData Import`")
	capkpi.rename_doc("DocType", "Data Import Beta", "Data Import")
