# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import capkpi


def add_custom_field(doctype, fieldname, fieldtype="Data", options=None):
	capkpi.get_doc(
		{
			"doctype": "Custom Field",
			"dt": doctype,
			"fieldname": fieldname,
			"fieldtype": fieldtype,
			"options": options,
		}
	).insert()


def clear_custom_fields(doctype):
	capkpi.db.sql("delete from `tabCustom Field` where dt=%s", doctype)
	capkpi.clear_cache(doctype=doctype)
