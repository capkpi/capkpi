# Copyright (c) 2021, CapKPI Technologies and contributors
# For license information, please see license.txt

import capkpi
from capkpi.model.document import Document


class FormTour(Document):
	pass


@capkpi.whitelist()
@capkpi.validate_and_sanitize_search_inputs
def get_docfield_list(doctype, txt, searchfield, start, page_len, filters):
	or_filters = [
		["fieldname", "like", "%" + txt + "%"],
		["label", "like", "%" + txt + "%"],
		["fieldtype", "like", "%" + txt + "%"],
	]

	parent_doctype = filters.pop("doctype")
	excluded_fieldtypes = ["Column Break"]
	excluded_fieldtypes += filters.get("excluded_fieldtypes", [])

	docfields = capkpi.get_all(
		doctype,
		fields=["name as value", "label", "fieldtype"],
		filters={"parent": parent_doctype, "fieldtype": ["not in", excluded_fieldtypes]},
		or_filters=or_filters,
		limit_start=start,
		limit_page_length=page_len,
		as_list=1,
	)
	return docfields
