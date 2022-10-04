# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# See license.txt

from __future__ import unicode_literals

import capkpi

no_cache = True


def get_context(context):
	token = capkpi.local.form_dict.token
	doc = capkpi.get_doc(capkpi.local.form_dict.doctype, capkpi.local.form_dict.docname)

	context.payment_message = ""
	if hasattr(doc, "get_payment_success_message"):
		context.payment_message = doc.get_payment_success_message()
