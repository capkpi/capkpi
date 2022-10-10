# Copyright (c) 2019, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import capkpi


@capkpi.whitelist()
def get_list_settings(doctype):
	try:
		return capkpi.get_cached_doc("List View Settings", doctype)
	except capkpi.DoesNotExistError:
		capkpi.clear_messages()


@capkpi.whitelist()
def set_list_settings(doctype, values):
	try:
		doc = capkpi.get_doc("List View Settings", doctype)
	except capkpi.DoesNotExistError:
		doc = capkpi.new_doc("List View Settings")
		doc.name = doctype
		capkpi.clear_messages()
	doc.update(capkpi.parse_json(values))
	doc.save()


@capkpi.whitelist()
def get_group_by_count(doctype, current_filters, field):
	current_filters = capkpi.parse_json(current_filters)
	subquery_condition = ""

	subquery = capkpi.get_all(doctype, filters=current_filters, return_query=True)
	if field == "assigned_to":
		subquery_condition = " and `tabToDo`.reference_name in ({subquery})".format(subquery=subquery)
		return capkpi.db.sql(
			"""select `tabToDo`.owner as name, count(*) as count
			from
				`tabToDo`, `tabUser`
			where
				`tabToDo`.status!='Cancelled' and
				`tabToDo`.owner = `tabUser`.name and
				`tabUser`.user_type = 'System User'
				{subquery_condition}
			group by
				`tabToDo`.owner
			order by
				count desc
			limit 50""".format(
				subquery_condition=subquery_condition
			),
			as_dict=True,
		)
	else:
		return capkpi.db.get_list(
			doctype,
			filters=current_filters,
			group_by="`tab{0}`.{1}".format(doctype, field),
			fields=["count(*) as count", "`{}` as name".format(field)],
			order_by="count desc",
			limit=50,
		)