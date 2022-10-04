# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import hashlib
import hmac

from six import string_types
from six.moves.urllib.parse import urlencode

import capkpi
import capkpi.utils
from capkpi import _


def get_signed_params(params):
	"""Sign a url by appending `&_signature=xxxxx` to given params (string or dict).

	:param params: String or dict of parameters."""
	if not isinstance(params, string_types):
		params = urlencode(params)

	signature = hmac.new(params.encode(), digestmod=hashlib.md5)
	signature.update(get_secret().encode())
	return params + "&_signature=" + signature.hexdigest()


def get_secret():
	return capkpi.local.conf.get("secret") or str(
		capkpi.db.get_value("User", "Administrator", "creation")
	)


def verify_request():
	"""Verify if the incoming signed request if it is correct."""
	query_string = capkpi.safe_decode(
		capkpi.local.flags.signed_query_string or getattr(capkpi.request, "query_string", None)
	)

	valid = False

	signature_string = "&_signature="
	if signature_string in query_string:
		params, signature = query_string.split(signature_string)

		given_signature = hmac.new(params.encode("utf-8"), digestmod=hashlib.md5)

		given_signature.update(get_secret().encode())
		valid = signature == given_signature.hexdigest()

	if not valid:
		capkpi.respond_as_web_page(
			_("Invalid Link"),
			_("This link is invalid or expired. Please make sure you have pasted correctly."),
		)

	return valid


def get_url(cmd, params, nonce=None, secret=None):
	if not nonce:
		nonce = params
	signature = get_signature(params, nonce, secret)
	params["signature"] = signature
	return capkpi.utils.get_url("".join(["api/method/", cmd, "?", urlencode(params)]))


def get_signature(params, nonce, secret=None):
	params = "".join((capkpi.utils.cstr(p) for p in params.values()))
	if not secret:
		secret = capkpi.local.conf.get("secret") or "secret"

	signature = hmac.new(str(nonce), digestmod=hashlib.md5)
	signature.update(secret)
	signature.update(params)
	return signature.hexdigest()


def verify_using_doc(doc, signature, cmd):
	params = doc.get_signature_params()
	return signature == get_signature(params, doc.get_nonce())


def get_url_using_doc(doc, cmd):
	params = doc.get_signature_params()
	return get_url(cmd, params, doc.get_nonce())
