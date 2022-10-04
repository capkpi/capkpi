# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals

import json

import capkpi
from capkpi import _
from capkpi.integrations.doctype.paytm_settings.paytm_settings import (
	get_paytm_config,
	get_paytm_params,
)


def get_context(context):
	context.no_cache = 1
	paytm_config = get_paytm_config()

	try:
		doc = capkpi.get_doc("Integration Request", capkpi.form_dict["order_id"])

		context.payment_details = get_paytm_params(json.loads(doc.data), doc.name, paytm_config)

		context.url = paytm_config.url

	except Exception:
		capkpi.log_error()
		capkpi.redirect_to_message(
			_("Invalid Token"),
			_("Seems token you are using is invalid!"),
			http_status_code=400,
			indicator_color="red",
		)

		capkpi.local.flags.redirect_location = capkpi.local.response.location
		raise capkpi.Redirect
