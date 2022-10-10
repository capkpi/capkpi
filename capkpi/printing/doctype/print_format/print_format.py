# -*- coding: utf-8 -*-
# Copyright (c) 2017, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json

import capkpi
import capkpi.utils
from capkpi import _
from capkpi.model.document import Document
from capkpi.utils.jinja import validate_template


class PrintFormat(Document):
	def validate(self):
		if (
			self.standard == "Yes"
			and not capkpi.local.conf.get("developer_mode")
			and not (capkpi.flags.in_import or capkpi.flags.in_test)
		):

			capkpi.throw(capkpi._("Standard Print Format cannot be updated"))

		# old_doc_type is required for clearing item cache
		self.old_doc_type = capkpi.db.get_value("Print Format", self.name, "doc_type")

		self.extract_images()

		if not self.module:
			self.module = capkpi.db.get_value("DocType", self.doc_type, "module")

		if self.html and self.print_format_type != "JS":
			validate_template(self.html)

		if self.custom_format and self.raw_printing and not self.raw_commands:
			capkpi.throw(
				_("{0} are required").format(capkpi.bold(_("Raw Commands"))), capkpi.MandatoryError
			)

		if self.custom_format and not self.html and not self.raw_printing:
			capkpi.throw(_("{0} is required").format(capkpi.bold(_("HTML"))), capkpi.MandatoryError)

	def extract_images(self):
		from capkpi.core.doctype.file.file import extract_images_from_html

		if self.format_data:
			data = json.loads(self.format_data)
			for df in data:
				if df.get("fieldtype") and df["fieldtype"] in ("HTML", "Custom HTML") and df.get("options"):
					df["options"] = extract_images_from_html(self, df["options"])
			self.format_data = json.dumps(data)

	def on_update(self):
		if hasattr(self, "old_doc_type") and self.old_doc_type:
			capkpi.clear_cache(doctype=self.old_doc_type)
		if self.doc_type:
			capkpi.clear_cache(doctype=self.doc_type)

		self.export_doc()

	def after_rename(self, old: str, new: str, *args, **kwargs):
		if self.doc_type:
			capkpi.clear_cache(doctype=self.doc_type)

		# update property setter default_print_format if set
		capkpi.db.set_value(
			"Property Setter",
			{
				"doctype_or_field": "DocType",
				"doc_type": self.doc_type,
				"property": "default_print_format",
				"value": old,
			},
			"value",
			new,
		)

	def export_doc(self):
		from capkpi.modules.utils import export_module_json

		export_module_json(self, self.standard == "Yes", self.module)

	def on_trash(self):
		if self.doc_type:
			capkpi.clear_cache(doctype=self.doc_type)


@capkpi.whitelist()
def make_default(name):
	"""Set print format as default"""
	capkpi.has_permission("Print Format", "write")

	print_format = capkpi.get_doc("Print Format", name)

	if (capkpi.conf.get("developer_mode") or 0) == 1:
		# developer mode, set it default in doctype
		doctype = capkpi.get_doc("DocType", print_format.doc_type)
		doctype.default_print_format = name
		doctype.save()
	else:
		# customization
		capkpi.make_property_setter(
			{
				"doctype_or_field": "DocType",
				"doctype": print_format.doc_type,
				"property": "default_print_format",
				"value": name,
			}
		)

	capkpi.msgprint(
		capkpi._("{0} is now default print format for {1} doctype").format(
			capkpi.bold(name), capkpi.bold(print_format.doc_type)
		)
	)
