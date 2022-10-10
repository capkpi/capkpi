# -*- coding: utf-8 -*-
# Copyright (c) 2020, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi.model.document import Document


class ListViewSettings(Document):
	def on_update(self):
		capkpi.clear_document_cache(self.doctype, self.name)


@capkpi.whitelist()
def save_listview_settings(doctype, listview_settings, removed_listview_fields):

	listview_settings = capkpi.parse_json(listview_settings)
	removed_listview_fields = capkpi.parse_json(removed_listview_fields)

	if capkpi.get_all("List View Settings", filters={"name": doctype}):
		doc = capkpi.get_doc("List View Settings", doctype)
		doc.update(listview_settings)
		doc.save()
	else:
		doc = capkpi.new_doc("List View Settings")
		doc.name = doctype
		doc.update(listview_settings)
		doc.insert()

	set_listview_fields(doctype, listview_settings.get("fields"), removed_listview_fields)

	return {"meta": capkpi.get_meta(doctype, False), "listview_settings": doc}


def set_listview_fields(doctype, listview_fields, removed_listview_fields):
	meta = capkpi.get_meta(doctype)

	listview_fields = [
		f.get("fieldname") for f in capkpi.parse_json(listview_fields) if f.get("fieldname")
	]

	for field in removed_listview_fields:
		set_in_list_view_property(doctype, meta.get_field(field), "0")

	for field in listview_fields:
		set_in_list_view_property(doctype, meta.get_field(field), "1")


def set_in_list_view_property(doctype, field, value):
	if not field or field.fieldname == "status_field":
		return

	property_setter = capkpi.db.get_value(
		"Property Setter",
		{"doc_type": doctype, "field_name": field.fieldname, "property": "in_list_view"},
	)
	if property_setter:
		doc = capkpi.get_doc("Property Setter", property_setter)
		doc.value = value
		doc.save()
	else:
		capkpi.make_property_setter(
			{
				"doctype": doctype,
				"doctype_or_field": "DocField",
				"fieldname": field.fieldname,
				"property": "in_list_view",
				"value": value,
				"property_type": "Check",
			},
			ignore_validate=True,
		)


@capkpi.whitelist()
def get_default_listview_fields(doctype):
	meta = capkpi.get_meta(doctype)
	path = capkpi.get_module_path(
		capkpi.scrub(meta.module), "doctype", capkpi.scrub(meta.name), capkpi.scrub(meta.name) + ".json"
	)
	doctype_json = capkpi.get_file_json(path)

	fields = [f.get("fieldname") for f in doctype_json.get("fields") if f.get("in_list_view")]

	if meta.title_field:
		if not meta.title_field.strip() in fields:
			fields.append(meta.title_field.strip())

	return fields
