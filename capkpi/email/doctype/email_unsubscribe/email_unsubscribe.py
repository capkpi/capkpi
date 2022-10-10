# -*- coding: utf-8 -*-
# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi import _
from capkpi.model.document import Document


class EmailUnsubscribe(Document):
	def validate(self):
		if not self.global_unsubscribe and not (self.reference_doctype and self.reference_name):
			capkpi.throw(_("Reference DocType and Reference Name are required"), capkpi.MandatoryError)

		if not self.global_unsubscribe and capkpi.db.get_value(
			self.doctype, self.name, "global_unsubscribe"
		):
			capkpi.throw(_("Delete this record to allow sending to this email address"))

		if self.global_unsubscribe:
			if capkpi.get_all(
				"Email Unsubscribe",
				filters={"email": self.email, "global_unsubscribe": 1, "name": ["!=", self.name]},
			):
				capkpi.throw(_("{0} already unsubscribed").format(self.email), capkpi.DuplicateEntryError)

		else:
			if capkpi.get_all(
				"Email Unsubscribe",
				filters={
					"email": self.email,
					"reference_doctype": self.reference_doctype,
					"reference_name": self.reference_name,
					"name": ["!=", self.name],
				},
			):
				capkpi.throw(
					_("{0} already unsubscribed for {1} {2}").format(
						self.email, self.reference_doctype, self.reference_name
					),
					capkpi.DuplicateEntryError,
				)

	def on_update(self):
		if self.reference_doctype and self.reference_name:
			doc = capkpi.get_doc(self.reference_doctype, self.reference_name)
			doc.add_comment("Label", _("Left this conversation"), comment_email=self.email)
