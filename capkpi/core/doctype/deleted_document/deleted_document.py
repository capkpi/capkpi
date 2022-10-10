# -*- coding: utf-8 -*-
# Copyright (c) 2015, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json

import capkpi
from capkpi import _
from capkpi.desk.doctype.bulk_update.bulk_update import show_progress
from capkpi.model.document import Document


class DeletedDocument(Document):
	pass


@capkpi.whitelist()
def restore(name, alert=True):
	deleted = capkpi.get_doc("Deleted Document", name)

	if deleted.restored:
		capkpi.throw(_("Document {0} Already Restored").format(name), exc=capkpi.DocumentAlreadyRestored)

	doc = capkpi.get_doc(json.loads(deleted.data))

	try:
		doc.insert()
	except capkpi.DocstatusTransitionError:
		capkpi.msgprint(_("Cancelled Document restored as Draft"))
		doc.docstatus = 0
		doc.insert()

	doc.add_comment("Edit", _("restored {0} as {1}").format(deleted.deleted_name, doc.name))

	deleted.new_name = doc.name
	deleted.restored = 1
	deleted.db_update()

	if alert:
		capkpi.msgprint(_("Document Restored"))


@capkpi.whitelist()
def bulk_restore(docnames):
	docnames = capkpi.parse_json(docnames)
	message = _("Restoring Deleted Document")
	restored, invalid, failed = [], [], []

	for i, d in enumerate(docnames):
		try:
			show_progress(docnames, message, i + 1, d)
			restore(d, alert=False)
			capkpi.db.commit()
			restored.append(d)

		except capkpi.DocumentAlreadyRestored:
			capkpi.message_log.pop()
			invalid.append(d)

		except Exception:
			capkpi.message_log.pop()
			failed.append(d)
			capkpi.db.rollback()

	return {"restored": restored, "invalid": invalid, "failed": failed}
