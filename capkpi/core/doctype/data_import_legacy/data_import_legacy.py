# -*- coding: utf-8 -*-
# Copyright (c) 2017, CapKPI Technologies and contributors
# For license information, please see license.txt

import os

import capkpi
import capkpi.modules.import_file
from capkpi import _
from capkpi.core.doctype.data_import_legacy.importer import upload
from capkpi.model.document import Document
from capkpi.modules.import_file import import_file_by_path as _import_file_by_path
from capkpi.utils.background_jobs import enqueue
from capkpi.utils.data import format_datetime


class DataImportLegacy(Document):
	def autoname(self):
		if not self.name:
			self.name = "Import on " + format_datetime(self.creation)

	def validate(self):
		if not self.import_file:
			self.db_set("total_rows", 0)
		if self.import_status == "In Progress":
			capkpi.throw(_("Can't save the form as data import is in progress."))

		# validate the template just after the upload
		# if there is total_rows in the doc, it means that the template is already validated and error free
		if self.import_file and not self.total_rows:
			upload(data_import_doc=self, from_data_import="Yes", validate_template=True)


@capkpi.whitelist()
def get_importable_doctypes():
	return capkpi.cache().hget("can_import", capkpi.session.user)


@capkpi.whitelist()
def import_data(data_import):
	capkpi.db.set_value(
		"Data Import Legacy", data_import, "import_status", "In Progress", update_modified=False
	)
	capkpi.publish_realtime(
		"data_import_progress",
		{"progress": "0", "data_import": data_import, "reload": True},
		user=capkpi.session.user,
	)

	from capkpi.core.page.background_jobs.background_jobs import get_info

	enqueued_jobs = [d.get("job_name") for d in get_info()]

	if data_import not in enqueued_jobs:
		enqueue(
			upload,
			queue="default",
			timeout=6000,
			event="data_import",
			job_name=data_import,
			data_import_doc=data_import,
			from_data_import="Yes",
			user=capkpi.session.user,
		)


def import_doc(
	path,
	overwrite=False,
	ignore_links=False,
	ignore_insert=False,
	insert=False,
	submit=False,
	pre_process=None,
):
	if os.path.isdir(path):
		files = [os.path.join(path, f) for f in os.listdir(path)]
	else:
		files = [path]

	for f in files:
		if f.endswith(".json"):
			capkpi.flags.mute_emails = True
			_import_file_by_path(
				f, data_import=True, force=True, pre_process=pre_process, reset_permissions=True
			)
			capkpi.flags.mute_emails = False
			capkpi.db.commit()
		elif f.endswith(".csv"):
			import_file_by_path(
				f, ignore_links=ignore_links, overwrite=overwrite, submit=submit, pre_process=pre_process
			)
			capkpi.db.commit()


def import_file_by_path(
	path, ignore_links=False, overwrite=False, submit=False, pre_process=None, no_email=True
):
	from capkpi.utils.csvutils import read_csv_content

	print("Importing " + path)
	with open(path, "r") as infile:
		upload(
			rows=read_csv_content(infile.read()),
			ignore_links=ignore_links,
			no_email=no_email,
			overwrite=overwrite,
			submit_after_import=submit,
			pre_process=pre_process,
		)


def export_json(doctype, path, filters=None, or_filters=None, name=None, order_by="creation asc"):
	def post_process(out):
		del_keys = ("modified_by", "creation", "owner", "idx")
		for doc in out:
			for key in del_keys:
				if key in doc:
					del doc[key]
			for k, v in doc.items():
				if isinstance(v, list):
					for child in v:
						for key in del_keys + ("docstatus", "doctype", "modified", "name"):
							if key in child:
								del child[key]

	out = []
	if name:
		out.append(capkpi.get_doc(doctype, name).as_dict())
	elif capkpi.db.get_value("DocType", doctype, "issingle"):
		out.append(capkpi.get_doc(doctype).as_dict())
	else:
		for doc in capkpi.get_all(
			doctype,
			fields=["name"],
			filters=filters,
			or_filters=or_filters,
			limit_page_length=0,
			order_by=order_by,
		):
			out.append(capkpi.get_doc(doctype, doc.name).as_dict())
	post_process(out)

	dirname = os.path.dirname(path)
	if not os.path.exists(dirname):
		path = os.path.join("..", path)

	with open(path, "w") as outfile:
		outfile.write(capkpi.as_json(out))


def export_csv(doctype, path):
	from capkpi.core.doctype.data_export.exporter import export_data

	with open(path, "wb") as csvfile:
		export_data(doctype=doctype, all_doctypes=True, template=True, with_data=True)
		csvfile.write(capkpi.response.result.encode("utf-8"))


@capkpi.whitelist()
def export_fixture(doctype, app):
	if capkpi.session.user != "Administrator":
		raise capkpi.PermissionError

	if not os.path.exists(capkpi.get_app_path(app, "fixtures")):
		os.mkdir(capkpi.get_app_path(app, "fixtures"))

	export_json(
		doctype,
		capkpi.get_app_path(app, "fixtures", capkpi.scrub(doctype) + ".json"),
		order_by="name asc",
	)
