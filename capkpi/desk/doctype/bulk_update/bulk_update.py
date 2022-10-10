# -*- coding: utf-8 -*-
# Copyright (c) 2015, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi import _
from capkpi.model.document import Document
from capkpi.utils import cint


class BulkUpdate(Document):
	pass


@capkpi.whitelist()
def update(doctype, field, value, condition="", limit=500):
	if not limit or cint(limit) > 500:
		limit = 500

	if condition:
		condition = " where " + condition

	if ";" in condition:
		capkpi.throw(_("; not allowed in condition"))

	docnames = capkpi.db.sql_list(
		"""select name from `tab{0}`{1} limit 0, {2}""".format(doctype, condition, limit)
	)
	data = {}
	data[field] = value
	return submit_cancel_or_update_docs(doctype, docnames, "update", data)


@capkpi.whitelist()
def submit_cancel_or_update_docs(doctype, docnames, action="submit", data=None):
	docnames = capkpi.parse_json(docnames)

	if data:
		data = capkpi.parse_json(data)

	failed = []

	for i, d in enumerate(docnames, 1):
		doc = capkpi.get_doc(doctype, d)
		try:
			message = ""
			if action == "submit" and doc.docstatus == 0:
				doc.submit()
				message = _("Submitting {0}").format(doctype)
			elif action == "cancel" and doc.docstatus == 1:
				doc.cancel()
				message = _("Cancelling {0}").format(doctype)
			elif action == "update" and doc.docstatus < 2:
				doc.update(data)
				doc.save()
				message = _("Updating {0}").format(doctype)
			else:
				failed.append(d)
			capkpi.db.commit()
			show_progress(docnames, message, i, d)

		except Exception:
			failed.append(d)
			capkpi.db.rollback()

	return failed


def show_progress(docnames, message, i, description):
	n = len(docnames)
	if n >= 10:
		capkpi.publish_progress(float(i) * 100 / n, title=message, description=description)
