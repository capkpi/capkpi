from __future__ import unicode_literals

import capkpi


def execute():
	if capkpi.db.table_exists("Prepared Report"):
		capkpi.reload_doc("core", "doctype", "prepared_report")
		prepared_reports = capkpi.get_all("Prepared Report")
		for report in prepared_reports:
			capkpi.delete_doc("Prepared Report", report.name)
