# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi
from capkpi.utils import strip_html_tags

no_cache = 1


def get_context(context):
	message_context = {}
	if hasattr(capkpi.local, "message"):
		message_context["header"] = capkpi.local.message_title
		message_context["title"] = strip_html_tags(capkpi.local.message_title)
		message_context["message"] = capkpi.local.message
		if hasattr(capkpi.local, "message_success"):
			message_context["success"] = capkpi.local.message_success

	elif capkpi.local.form_dict.id:
		message_id = capkpi.local.form_dict.id
		key = "message_id:{0}".format(message_id)
		message = capkpi.cache().get_value(key, expires=True)
		if message:
			message_context.update(message.get("context", {}))
			if message.get("http_status_code"):
				capkpi.local.response["http_status_code"] = message["http_status_code"]

	return message_context
