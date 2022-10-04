# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

from six.moves.urllib.parse import parse_qsl

import capkpi
from capkpi import _
from capkpi.twofactor import get_qr_svg_code


def get_context(context):
	context.no_cache = 1
	context.qr_code_user, context.qrcode_svg = get_user_svg_from_cache()


def get_query_key():
	"""Return query string arg."""
	query_string = capkpi.local.request.query_string
	query = dict(parse_qsl(query_string))
	query = {key.decode(): val.decode() for key, val in query.items()}
	if not "k" in list(query):
		capkpi.throw(_("Not Permitted"), capkpi.PermissionError)
	query = (query["k"]).strip()
	if False in [i.isalpha() or i.isdigit() for i in query]:
		capkpi.throw(_("Not Permitted"), capkpi.PermissionError)
	return query


def get_user_svg_from_cache():
	"""Get User and SVG code from cache."""
	key = get_query_key()
	totp_uri = capkpi.cache().get_value("{}_uri".format(key))
	user = capkpi.cache().get_value("{}_user".format(key))
	if not totp_uri or not user:
		capkpi.throw(_("Page has expired!"), capkpi.PermissionError)
	if not capkpi.db.exists("User", user):
		capkpi.throw(_("Not Permitted"), capkpi.PermissionError)
	user = capkpi.get_doc("User", user)
	svg = get_qr_svg_code(totp_uri)
	return (user, svg.decode())
