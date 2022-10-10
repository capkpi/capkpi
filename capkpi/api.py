# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import base64
import binascii
import json
from urllib.parse import urlencode, urlparse

import capkpi
import capkpi.client
import capkpi.handler
from capkpi import _
from capkpi.utils.data import sbool
from capkpi.utils.response import build_response


def handle():
	"""
	Handler for `/api` methods

	### Examples:

	`/api/method/{methodname}` will call a whitelisted method

	`/api/resource/{doctype}` will query a table
	        examples:
	        - `?fields=["name", "owner"]`
	        - `?filters=[["Task", "name", "like", "%005"]]`
	        - `?limit_start=0`
	        - `?limit_page_length=20`

	`/api/resource/{doctype}/{name}` will point to a resource
	        `GET` will return doclist
	        `POST` will insert
	        `PUT` will update
	        `DELETE` will delete

	`/api/resource/{doctype}/{name}?run_method={method}` will run a whitelisted controller method
	"""

	parts = capkpi.request.path[1:].split("/", 3)
	call = doctype = name = None

	if len(parts) > 1:
		call = parts[1]

	if len(parts) > 2:
		doctype = parts[2]

	if len(parts) > 3:
		name = parts[3]

	if call == "method":
		capkpi.local.form_dict.cmd = doctype
		return capkpi.handler.handle()

	elif call == "resource":
		if "run_method" in capkpi.local.form_dict:
			method = capkpi.local.form_dict.pop("run_method")
			doc = capkpi.get_doc(doctype, name)
			doc.is_whitelisted(method)

			if capkpi.local.request.method == "GET":
				if not doc.has_permission("read"):
					capkpi.throw(_("Not permitted"), capkpi.PermissionError)
				capkpi.local.response.update({"data": doc.run_method(method, **capkpi.local.form_dict)})

			if capkpi.local.request.method == "POST":
				if not doc.has_permission("write"):
					capkpi.throw(_("Not permitted"), capkpi.PermissionError)

				capkpi.local.response.update({"data": doc.run_method(method, **capkpi.local.form_dict)})
				capkpi.db.commit()

		else:
			if name:
				if capkpi.local.request.method == "GET":
					doc = capkpi.get_doc(doctype, name)
					if not doc.has_permission("read"):
						raise capkpi.PermissionError
					capkpi.local.response.update({"data": doc})

				if capkpi.local.request.method == "PUT":
					data = get_request_form_data()

					doc = capkpi.get_doc(doctype, name, for_update=True)

					if "flags" in data:
						del data["flags"]

					# Not checking permissions here because it's checked in doc.save
					doc.update(data)

					capkpi.local.response.update({"data": doc.save().as_dict()})

					if doc.parenttype and doc.parent:
						capkpi.get_doc(doc.parenttype, doc.parent).save()

					capkpi.db.commit()

				if capkpi.local.request.method == "DELETE":
					# Not checking permissions here because it's checked in delete_doc
					capkpi.delete_doc(doctype, name, ignore_missing=False)
					capkpi.local.response.http_status_code = 202
					capkpi.local.response.message = "ok"
					capkpi.db.commit()

			elif doctype:
				if capkpi.local.request.method == "GET":
					# set fields for capkpi.get_list
					if capkpi.local.form_dict.get("fields"):
						capkpi.local.form_dict["fields"] = json.loads(capkpi.local.form_dict["fields"])

					# set limit of records for capkpi.get_list
					capkpi.local.form_dict.setdefault(
						"limit_page_length",
						capkpi.local.form_dict.limit or capkpi.local.form_dict.limit_page_length or 20,
					)

					# convert strings to native types - only as_dict and debug accept bool
					for param in ["as_dict", "debug"]:
						param_val = capkpi.local.form_dict.get(param)
						if param_val is not None:
							capkpi.local.form_dict[param] = sbool(param_val)

					# evaluate capkpi.get_list
					data = capkpi.call(capkpi.client.get_list, doctype, **capkpi.local.form_dict)

					# set capkpi.get_list result to response
					capkpi.local.response.update({"data": data})

				if capkpi.local.request.method == "POST":
					# fetch data from from dict
					data = get_request_form_data()
					data.update({"doctype": doctype})

					# insert document from request data
					doc = capkpi.get_doc(data).insert()

					# set response data
					capkpi.local.response.update({"data": doc.as_dict()})

					# commit for POST requests
					capkpi.db.commit()
			else:
				raise capkpi.DoesNotExistError

	else:
		raise capkpi.DoesNotExistError

	return build_response("json")


def get_request_form_data():
	if capkpi.local.form_dict.data is None:
		data = capkpi.safe_decode(capkpi.local.request.get_data())
	else:
		data = capkpi.local.form_dict.data

	return capkpi.parse_json(data)


def validate_auth():
	"""
	Authenticate and sets user for the request.
	"""
	authorization_header = capkpi.get_request_header("Authorization", str()).split(" ")

	if len(authorization_header) == 2:
		validate_oauth(authorization_header)
		validate_auth_via_api_keys(authorization_header)

	validate_auth_via_hooks()


def validate_oauth(authorization_header):
	"""
	Authenticate request using OAuth and set session user

	Args:
	        authorization_header (list of str): The 'Authorization' header containing the prefix and token
	"""

	from capkpi.integrations.oauth2 import get_oauth_server
	from capkpi.oauth import get_url_delimiter

	form_dict = capkpi.local.form_dict
	token = authorization_header[1]
	req = capkpi.request
	parsed_url = urlparse(req.url)
	access_token = {"access_token": token}
	uri = (
		parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path + "?" + urlencode(access_token)
	)
	http_method = req.method
	headers = req.headers
	body = req.get_data()
	if req.content_type and "multipart/form-data" in req.content_type:
		body = None

	try:
		required_scopes = capkpi.db.get_value("OAuth Bearer Token", token, "scopes").split(
			get_url_delimiter()
		)
		valid, oauthlib_request = get_oauth_server().verify_request(
			uri, http_method, body, headers, required_scopes
		)
		if valid:
			capkpi.set_user(capkpi.db.get_value("OAuth Bearer Token", token, "user"))
			capkpi.local.form_dict = form_dict
	except AttributeError:
		pass


def validate_auth_via_api_keys(authorization_header):
	"""
	Authenticate request using API keys and set session user

	Args:
	        authorization_header (list of str): The 'Authorization' header containing the prefix and token
	"""

	try:
		auth_type, auth_token = authorization_header
		authorization_source = capkpi.get_request_header("CapKPI-Authorization-Source")
		if auth_type.lower() == "basic":
			api_key, api_secret = capkpi.safe_decode(base64.b64decode(auth_token)).split(":")
			validate_api_key_secret(api_key, api_secret, authorization_source)
		elif auth_type.lower() == "token":
			api_key, api_secret = auth_token.split(":")
			validate_api_key_secret(api_key, api_secret, authorization_source)
	except binascii.Error:
		capkpi.throw(
			_("Failed to decode token, please provide a valid base64-encoded token."),
			capkpi.InvalidAuthorizationToken,
		)
	except (AttributeError, TypeError, ValueError):
		pass


def validate_api_key_secret(api_key, api_secret, capkpi_authorization_source=None):
	"""capkpi_authorization_source to provide api key and secret for a doctype apart from User"""
	doctype = capkpi_authorization_source or "User"
	doc = capkpi.db.get_value(doctype=doctype, filters={"api_key": api_key}, fieldname=["name"])
	form_dict = capkpi.local.form_dict
	doc_secret = capkpi.utils.password.get_decrypted_password(doctype, doc, fieldname="api_secret")
	if api_secret == doc_secret:
		if doctype == "User":
			user = capkpi.db.get_value(doctype="User", filters={"api_key": api_key}, fieldname=["name"])
		else:
			user = capkpi.db.get_value(doctype, doc, "user")
		if capkpi.local.login_manager.user in ("", "Guest"):
			capkpi.set_user(user)
		capkpi.local.form_dict = form_dict


def validate_auth_via_hooks():
	for auth_hook in capkpi.get_hooks("auth_hooks", []):
		capkpi.get_attr(auth_hook)()