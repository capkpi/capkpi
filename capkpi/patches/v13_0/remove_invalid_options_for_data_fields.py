# Copyright (c) 2022, CapKPI and Contributors
# License: MIT. See LICENSE


import capkpi
from capkpi.model import data_field_options


def execute():
	custom_field = capkpi.qb.DocType("Custom Field")
	(
		capkpi.qb.update(custom_field)
		.set(custom_field.options, None)
		.where((custom_field.fieldtype == "Data") & (custom_field.options.notin(data_field_options)))
	).run()
