# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import json

from six import string_types

import capkpi
import capkpi.desk.form.load
import capkpi.desk.form.meta
from capkpi import _
from capkpi.core.doctype.file.file import extract_images_from_html
from capkpi.desk.form.document_follow import follow_document


@capkpi.whitelist()
def remove_attach():
	"""remove attachment"""
	fid = capkpi.form_dict.get("fid")
	file_name = capkpi.form_dict.get("file_name")
	capkpi.delete_doc("File", fid)


@capkpi.whitelist()
def add_comment(reference_doctype, reference_name, content, comment_email, comment_by):
	"""allow any logged user to post a comment"""
	doc = capkpi.get_doc(
		dict(
			doctype="Comment",
			reference_doctype=reference_doctype,
			reference_name=reference_name,
			comment_email=comment_email,
			comment_type="Comment",
			comment_by=comment_by,
		)
	)
	reference_doc = capkpi.get_doc(reference_doctype, reference_name)
	doc.content = extract_images_from_html(reference_doc, content, is_private=True)
	doc.insert(ignore_permissions=True)

	follow_document(doc.reference_doctype, doc.reference_name, capkpi.session.user)
	return doc.as_dict()


@capkpi.whitelist()
def update_comment(name, content):
	"""allow only owner to update comment"""
	doc = capkpi.get_doc("Comment", name)

	if capkpi.session.user not in ["Administrator", doc.owner]:
		capkpi.throw(_("Comment can only be edited by the owner"), capkpi.PermissionError)

	doc.content = content
	doc.save(ignore_permissions=True)


@capkpi.whitelist()
def get_next(doctype, value, prev, filters=None, sort_order="desc", sort_field="modified"):

	prev = int(prev)
	if not filters:
		filters = []
	if isinstance(filters, string_types):
		filters = json.loads(filters)

	# # condition based on sort order
	condition = ">" if sort_order.lower() == "asc" else "<"

	# switch the condition
	if prev:
		sort_order = "asc" if sort_order.lower() == "desc" else "desc"
		condition = "<" if condition == ">" else ">"

	# # add condition for next or prev item
	filters.append([doctype, sort_field, condition, capkpi.get_value(doctype, value, sort_field)])

	res = capkpi.get_list(
		doctype,
		fields=["name"],
		filters=filters,
		order_by="`tab{0}`.{1}".format(doctype, sort_field) + " " + sort_order,
		limit_start=0,
		limit_page_length=1,
		as_list=True,
	)

	if not res:
		capkpi.msgprint(_("No further records"))
		return None
	else:
		return res[0][0]


def get_pdf_link(doctype, docname, print_format="Standard", no_letterhead=0):
	return "/api/method/capkpi.utils.print_format.download_pdf?doctype={doctype}&name={docname}&format={print_format}&no_letterhead={no_letterhead}".format(
		doctype=doctype, docname=docname, print_format=print_format, no_letterhead=no_letterhead
	)
