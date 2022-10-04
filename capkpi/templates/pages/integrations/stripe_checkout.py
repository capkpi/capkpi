# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals

import json

import capkpi
from capkpi import _
from capkpi.integrations.doctype.stripe_settings.stripe_settings import get_gateway_controller
from capkpi.utils import cint, fmt_money

no_cache = 1

expected_keys = (
	"amount",
	"title",
	"description",
	"reference_doctype",
	"reference_docname",
	"payer_name",
	"payer_email",
	"order_id",
	"currency",
)


def get_context(context):
	context.no_cache = 1

	# all these keys exist in form_dict
	if not (set(expected_keys) - set(list(capkpi.form_dict))):
		for key in expected_keys:
			context[key] = capkpi.form_dict[key]

		gateway_controller = get_gateway_controller(context.reference_doctype, context.reference_docname)
		context.publishable_key = get_api_key(context.reference_docname, gateway_controller)
		context.image = get_header_image(context.reference_docname, gateway_controller)

		context["amount"] = fmt_money(amount=context["amount"], currency=context["currency"])

		if is_a_subscription(context.reference_doctype, context.reference_docname):
			payment_plan = capkpi.db.get_value(
				context.reference_doctype, context.reference_docname, "payment_plan"
			)
			recurrence = capkpi.db.get_value("Payment Plan", payment_plan, "recurrence")

			context["amount"] = context["amount"] + " " + _(recurrence)

	else:
		capkpi.redirect_to_message(
			_("Some information is missing"),
			_("Looks like someone sent you to an incomplete URL. Please ask them to look into it."),
		)
		capkpi.local.flags.redirect_location = capkpi.local.response.location
		raise capkpi.Redirect


def get_api_key(doc, gateway_controller):
	publishable_key = capkpi.db.get_value("Stripe Settings", gateway_controller, "publishable_key")
	if cint(capkpi.form_dict.get("use_sandbox")):
		publishable_key = capkpi.conf.sandbox_publishable_key

	return publishable_key


def get_header_image(doc, gateway_controller):
	header_image = capkpi.db.get_value("Stripe Settings", gateway_controller, "header_img")

	return header_image


@capkpi.whitelist(allow_guest=True)
def make_payment(stripe_token_id, data, reference_doctype=None, reference_docname=None):
	data = json.loads(data)

	data.update({"stripe_token_id": stripe_token_id})

	gateway_controller = get_gateway_controller(reference_doctype, reference_docname)

	if is_a_subscription(reference_doctype, reference_docname):
		reference = capkpi.get_doc(reference_doctype, reference_docname)
		data = reference.create_subscription("stripe", gateway_controller, data)
	else:
		data = capkpi.get_doc("Stripe Settings", gateway_controller).create_request(data)

	capkpi.db.commit()
	return data


def is_a_subscription(reference_doctype, reference_docname):
	if not capkpi.get_meta(reference_doctype).has_field("is_a_subscription"):
		return False
	return capkpi.db.get_value(reference_doctype, reference_docname, "is_a_subscription")
