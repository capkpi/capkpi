from __future__ import unicode_literals

import capkpi


def execute():
	column = "apply_user_permissions"
	to_remove = ["DocPerm", "Custom DocPerm"]

	for doctype in to_remove:
		if capkpi.db.table_exists(doctype):
			if column in capkpi.db.get_table_columns(doctype):
				capkpi.db.sql("alter table `tab{0}` drop column {1}".format(doctype, column))

	capkpi.reload_doc("core", "doctype", "docperm", force=True)
	capkpi.reload_doc("core", "doctype", "custom_docperm", force=True)
