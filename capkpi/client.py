# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import json
import os

from six import integer_types, iteritems, string_types

import capkpi
import capkpi.model
import capkpi.utils
from capkpi import _
from capkpi.desk.reportview import validate_args
from capkpi.model.db_query import check_parent_permission
from capkpi.utils import get_safe_filters

"""
Handle RESTful requests that are mapped to the `/api/resource` route.

Requests via CapKPIClient are also handled here.
"""


@capkpi.whitelist()
def get_list(
	doctype,
	fields=None,
	filters=None,
	order_by=None,
	limit_start=None,
	limit_page_length=20,
	parent=None,
	debug=False,
	as_dict=True,
	or_filters=None,
):
	"""Returns a list of records by filters, fields, ordering and limit

	:param doctype: DocType of the data to be queried
	:param fields: fields to be returned. Default is `name`
	:param filters: filter list by this dict
	:param order_by: Order by this fieldname
	:param limit_start: Start at this index
	:param limit_page_length: Number of records to be returned (default 20)"""
	if capkpi.is_table(doctype):
		check_parent_permission(parent, doctype)

	args = capkpi._dict(
		doctype=doctype,
		fields=fields,
		filters=filters,
		or_filters=or_filters,
		order_by=order_by,
		limit_start=limit_start,
		limit_page_length=limit_page_length,
		debug=debug,
		as_list=not as_dict,
	)

	validate_args(args)
	return capkpi.get_list(**args)


@capkpi.whitelist()
def get_count(doctype, filters=None, debug=False, cache=False):
	return capkpi.db.count(doctype, get_safe_filters(filters), debug, cache)


@capkpi.whitelist()
def get(doctype, name=None, filters=None, parent=None):
	"""Returns a document by name or filters

	:param doctype: DocType of the document to be returned
	:param name: return document of this `name`
	:param filters: If name is not set, filter by these values and return the first match"""
	if capkpi.is_table(doctype):
		check_parent_permission(parent, doctype)

	if name:
		doc = capkpi.get_doc(doctype, name)
	elif filters or filters == {}:
		doc = capkpi.get_doc(doctype, capkpi.parse_json(filters))
	else:
		doc = capkpi.get_doc(doctype)  # single

	doc.check_permission()
	return doc.as_dict()


@capkpi.whitelist()
def get_value(doctype, fieldname, filters=None, as_dict=True, debug=False, parent=None):
	"""Returns a value form a document

	:param doctype: DocType to be queried
	:param fieldname: Field to be returned (default `name`)
	:param filters: dict or string for identifying the record"""
	if capkpi.is_table(doctype):
		check_parent_permission(parent, doctype)

	if not capkpi.has_permission(doctype):
		capkpi.throw(_("No permission for {0}").format(_(doctype)), capkpi.PermissionError)

	filters = get_safe_filters(filters)
	if isinstance(filters, string_types):
		filters = {"name": filters}

	try:
		fields = capkpi.parse_json(fieldname)
	except (TypeError, ValueError):
		# name passed, not json
		fields = [fieldname]

	# check whether the used filters were really parseable and usable
	# and did not just result in an empty string or dict
	if not filters:
		filters = None

	if capkpi.get_meta(doctype).issingle:
		value = capkpi.db.get_values_from_single(fields, filters, doctype, as_dict=as_dict, debug=debug)
	else:
		value = get_list(
			doctype,
			filters=filters,
			fields=fields,
			debug=debug,
			limit_page_length=1,
			parent=parent,
			as_dict=as_dict,
		)

	if as_dict:
		return value[0] if value else {}

	if not value:
		return

	return value[0] if len(fields) > 1 else value[0][0]


@capkpi.whitelist()
def get_single_value(doctype, field):
	if not capkpi.has_permission(doctype):
		capkpi.throw(_("No permission for {0}").format(_(doctype)), capkpi.PermissionError)

	return capkpi.db.get_single_value(doctype, field)


@capkpi.whitelist(methods=["POST", "PUT"])
def set_value(doctype, name, fieldname, value=None):
	"""Set a value using get_doc, group of values

	:param doctype: DocType of the document
	:param name: name of the document
	:param fieldname: fieldname string or JSON / dict with key value pair
	:param value: value if fieldname is JSON / dict"""

	if fieldname != "idx" and fieldname in capkpi.model.default_fields:
		capkpi.throw(_("Cannot edit standard fields"))

	if not value:
		values = fieldname
		if isinstance(fieldname, string_types):
			try:
				values = json.loads(fieldname)
			except ValueError:
				values = {fieldname: ""}
	else:
		values = {fieldname: value}

	doc = capkpi.db.get_value(doctype, name, ["parenttype", "parent"], as_dict=True)
	if doc and doc.parent and doc.parenttype:
		doc = capkpi.get_doc(doc.parenttype, doc.parent)
		child = doc.getone({"doctype": doctype, "name": name})
		child.update(values)
	else:
		doc = capkpi.get_doc(doctype, name)
		doc.update(values)

	doc.save()

	return doc.as_dict()


@capkpi.whitelist(methods=["POST", "PUT"])
def insert(doc=None):
	"""Insert a document

	:param doc: JSON or dict object to be inserted"""
	if isinstance(doc, string_types):
		doc = json.loads(doc)

	if doc.get("parent") and doc.get("parenttype"):
		# inserting a child record
		parent = capkpi.get_doc(doc.get("parenttype"), doc.get("parent"))
		parent.append(doc.get("parentfield"), doc)
		parent.save()
		return parent.as_dict()
	else:
		doc = capkpi.get_doc(doc).insert()
		return doc.as_dict()


@capkpi.whitelist(methods=["POST", "PUT"])
def insert_many(docs=None):
	"""Insert multiple documents

	:param docs: JSON or list of dict objects to be inserted in one request"""
	if isinstance(docs, string_types):
		docs = json.loads(docs)

	out = []

	if len(docs) > 200:
		capkpi.throw(_("Only 200 inserts allowed in one request"))

	for doc in docs:
		if doc.get("parent") and doc.get("parenttype"):
			# inserting a child record
			parent = capkpi.get_doc(doc.get("parenttype"), doc.get("parent"))
			parent.append(doc.get("parentfield"), doc)
			parent.save()
			out.append(parent.name)
		else:
			doc = capkpi.get_doc(doc).insert()
			out.append(doc.name)

	return out


@capkpi.whitelist(methods=["POST", "PUT"])
def save(doc):
	"""Update (save) an existing document

	:param doc: JSON or dict object with the properties of the document to be updated"""
	if isinstance(doc, string_types):
		doc = json.loads(doc)

	doc = capkpi.get_doc(doc)
	doc.save()

	return doc.as_dict()


@capkpi.whitelist(methods=["POST", "PUT"])
def rename_doc(doctype, old_name, new_name, merge=False):
	"""Rename document

	:param doctype: DocType of the document to be renamed
	:param old_name: Current `name` of the document to be renamed
	:param new_name: New `name` to be set"""
	new_name = capkpi.rename_doc(doctype, old_name, new_name, merge=merge)
	return new_name


@capkpi.whitelist(methods=["POST", "PUT"])
def submit(doc):
	"""Submit a document

	:param doc: JSON or dict object to be submitted remotely"""
	if isinstance(doc, string_types):
		doc = json.loads(doc)

	doc = capkpi.get_doc(doc)
	doc.submit()

	return doc.as_dict()


@capkpi.whitelist(methods=["POST", "PUT"])
def cancel(doctype, name):
	"""Cancel a document

	:param doctype: DocType of the document to be cancelled
	:param name: name of the document to be cancelled"""
	wrapper = capkpi.get_doc(doctype, name)
	wrapper.cancel()

	return wrapper.as_dict()


@capkpi.whitelist(methods=["DELETE", "POST"])
def delete(doctype, name):
	"""Delete a remote document

	:param doctype: DocType of the document to be deleted
	:param name: name of the document to be deleted"""
	capkpi.delete_doc(doctype, name, ignore_missing=False)


@capkpi.whitelist(methods=["POST", "PUT"])
def bulk_update(docs):
	"""Bulk update documents

	:param docs: JSON list of documents to be updated remotely. Each document must have `docname` property"""
	docs = json.loads(docs)
	failed_docs = []
	for doc in docs:
		doc.pop("flags", None)
		try:
			existing_doc = capkpi.get_doc(doc["doctype"], doc["docname"])
			existing_doc.update(doc)
			existing_doc.save()
		except Exception:
			failed_docs.append({"doc": doc, "exc": capkpi.utils.get_traceback()})

	return {"failed_docs": failed_docs}


@capkpi.whitelist()
def has_permission(doctype, docname, perm_type="read"):
	"""Returns a JSON with data whether the document has the requested permission

	:param doctype: DocType of the document to be checked
	:param docname: `name` of the document to be checked
	:param perm_type: one of `read`, `write`, `create`, `submit`, `cancel`, `report`. Default is `read`"""
	# perm_type can be one of read, write, create, submit, cancel, report
	return {"has_permission": capkpi.has_permission(doctype, perm_type.lower(), docname)}


@capkpi.whitelist()
def get_password(doctype, name, fieldname):
	"""Return a password type property. Only applicable for System Managers

	:param doctype: DocType of the document that holds the password
	:param name: `name` of the document that holds the password
	:param fieldname: `fieldname` of the password property
	"""
	capkpi.only_for("System Manager")
	return capkpi.get_doc(doctype, name).get_password(fieldname)


@capkpi.whitelist()
def get_js(items):
	"""Load JS code files.  Will also append translations
	and extend `capkpi._messages`

	:param items: JSON list of paths of the js files to be loaded."""
	items = json.loads(items)
	out = []
	for src in items:
		src = src.strip("/").split("/")

		if ".." in src or src[0] != "assets":
			capkpi.throw(_("Invalid file path: {0}").format("/".join(src)))

		contentpath = os.path.join(capkpi.local.sites_path, *src)
		with open(contentpath, "r") as srcfile:
			code = capkpi.utils.cstr(srcfile.read())

		if capkpi.local.lang != "en":
			messages = capkpi.get_lang_dict("jsfile", contentpath)
			messages = json.dumps(messages)
			code += "\n\n$.extend(capkpi._messages, {})".format(messages)

		out.append(code)

	return out


@capkpi.whitelist(allow_guest=True)
def get_time_zone():
	"""Returns default time zone"""
	return {"time_zone": capkpi.defaults.get_defaults().get("time_zone")}


@capkpi.whitelist(methods=["POST", "PUT"])
def attach_file(
	filename=None,
	filedata=None,
	doctype=None,
	docname=None,
	folder=None,
	decode_base64=False,
	is_private=None,
	docfield=None,
):
	"""Attach a file to Document (POST)

	:param filename: filename e.g. test-file.txt
	:param filedata: base64 encode filedata which must be urlencoded
	:param doctype: Reference DocType to attach file to
	:param docname: Reference DocName to attach file to
	:param folder: Folder to add File into
	:param decode_base64: decode filedata from base64 encode, default is False
	:param is_private: Attach file as private file (1 or 0)
	:param docfield: file to attach to (optional)"""

	request_method = capkpi.local.request.environ.get("REQUEST_METHOD")

	if request_method.upper() != "POST":
		capkpi.throw(_("Invalid Request"))

	doc = capkpi.get_doc(doctype, docname)

	if not doc.has_permission():
		capkpi.throw(_("Not permitted"), capkpi.PermissionError)

	_file = capkpi.get_doc(
		{
			"doctype": "File",
			"file_name": filename,
			"attached_to_doctype": doctype,
			"attached_to_name": docname,
			"attached_to_field": docfield,
			"folder": folder,
			"is_private": is_private,
			"content": filedata,
			"decode": decode_base64,
		}
	)
	_file.save()

	if docfield and doctype:
		doc.set(docfield, _file.file_url)
		doc.save()

	return _file.as_dict()


@capkpi.whitelist()
def is_document_amended(doctype, docname):
	if capkpi.permissions.has_permission(doctype):
		try:
			return capkpi.db.exists(doctype, {"amended_from": docname})
		except capkpi.db.InternalError:
			pass

	return False


@capkpi.whitelist()
def validate_link(doctype: str, docname: str, fields=None):
	if not isinstance(doctype, str):
		capkpi.throw(_("DocType must be a string"))

	if not isinstance(docname, str):
		capkpi.throw(_("Document Name must be a string"))

	if doctype != "DocType" and not (
		capkpi.has_permission(doctype, "select") or capkpi.has_permission(doctype, "read")
	):
		capkpi.throw(
			_("You do not have Read or Select Permissions for {}").format(capkpi.bold(doctype)),
			capkpi.PermissionError,
		)

	values = capkpi._dict()
	values.name = capkpi.db.get_value(doctype, docname, cache=True)

	fields = capkpi.parse_json(fields)
	if not values.name or not fields:
		return values

	try:
		values.update(get_value(doctype, fields, docname))
	except capkpi.PermissionError:
		capkpi.clear_last_message()
		capkpi.msgprint(
			_("You need {0} permission to fetch values from {1} {2}").format(
				capkpi.bold(_("Read")), capkpi.bold(doctype), capkpi.bold(docname)
			),
			title=_("Cannot Fetch Values"),
			indicator="orange",
		)

	return values
