# -*- coding: utf-8 -*-
# Copyright (c) 2020, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi import _
from capkpi.model.document import Document
from capkpi.model.naming import parse_naming_series
from capkpi.utils.data import evaluate_filters


class DocumentNamingRule(Document):
	def validate(self):
		self.validate_fields_in_conditions()

	def validate_fields_in_conditions(self):
		if self.has_value_changed("document_type"):
			docfields = [x.fieldname for x in capkpi.get_meta(self.document_type).fields]
			for condition in self.conditions:
				if condition.field not in docfields:
					capkpi.throw(
						_("{0} is not a field of doctype {1}").format(
							capkpi.bold(condition.field), capkpi.bold(self.document_type)
						)
					)

	def apply(self, doc):
		"""
		Apply naming rules for the given document. Will set `name` if the rule is matched.
		"""
		if self.conditions:
			if not evaluate_filters(
				doc, [(self.document_type, d.field, d.condition, d.value) for d in self.conditions]
			):
				return

		counter = capkpi.db.get_value(self.doctype, self.name, "counter", for_update=True) or 0
		naming_series = parse_naming_series(self.prefix, doc=doc)

		doc.name = naming_series + ("%0" + str(self.prefix_digits) + "d") % (counter + 1)
		capkpi.db.set_value(self.doctype, self.name, "counter", counter + 1)


@capkpi.whitelist()
def update_current(name, new_counter):
	capkpi.only_for("System Manager")
	capkpi.db.set_value("Document Naming Rule", name, "counter", new_counter)