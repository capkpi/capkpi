# -*- coding: utf-8 -*-
# Copyright (c) 2019, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi.model.document import Document
from capkpi.utils import unique


class Tag(Document):
	pass


def check_user_tags(dt):
	"if the user does not have a tags column, then it creates one"
	try:
		capkpi.db.sql("select `_user_tags` from `tab%s` limit 1" % dt)
	except Exception as e:
		if capkpi.db.is_column_missing(e):
			DocTags(dt).setup()


@capkpi.whitelist()
def add_tag(tag, dt, dn, color=None):
	"adds a new tag to a record, and creates the Tag master"
	DocTags(dt).add(dn, tag)

	return tag


@capkpi.whitelist()
def add_tags(tags, dt, docs, color=None):
	"adds a new tag to a record, and creates the Tag master"
	tags = capkpi.parse_json(tags)
	docs = capkpi.parse_json(docs)
	for doc in docs:
		for tag in tags:
			DocTags(dt).add(doc, tag)

	# return tag


@capkpi.whitelist()
def remove_tag(tag, dt, dn):
	"removes tag from the record"
	DocTags(dt).remove(dn, tag)


@capkpi.whitelist()
def get_tagged_docs(doctype, tag):
	capkpi.has_permission(doctype, throw=True)

	return capkpi.db.sql(
		"""SELECT name
		FROM `tab{0}`
		WHERE _user_tags LIKE '%{1}%'""".format(
			doctype, tag
		)
	)


@capkpi.whitelist()
def get_tags(doctype, txt):
	tag = capkpi.get_list("Tag", filters=[["name", "like", "%{}%".format(txt)]])
	tags = [t.name for t in tag]

	return sorted(filter(lambda t: t and txt.lower() in t.lower(), list(set(tags))))


class DocTags:
	"""Tags for a particular doctype"""

	def __init__(self, dt):
		self.dt = dt

	def get_tag_fields(self):
		"""returns tag_fields property"""
		return capkpi.db.get_value("DocType", self.dt, "tag_fields")

	def get_tags(self, dn):
		"""returns tag for a particular item"""
		return (capkpi.db.get_value(self.dt, dn, "_user_tags", ignore=1) or "").strip()

	def add(self, dn, tag):
		"""add a new user tag"""
		tl = self.get_tags(dn).split(",")
		if not tag in tl:
			tl.append(tag)
			if not capkpi.db.exists("Tag", tag):
				capkpi.get_doc({"doctype": "Tag", "name": tag}).insert(ignore_permissions=True)
			self.update(dn, tl)

	def remove(self, dn, tag):
		"""remove a user tag"""
		tl = self.get_tags(dn).split(",")
		self.update(dn, filter(lambda x: x.lower() != tag.lower(), tl))

	def remove_all(self, dn):
		"""remove all user tags (call before delete)"""
		self.update(dn, [])

	def update(self, dn, tl):
		"""updates the _user_tag column in the table"""

		if not tl:
			tags = ""
		else:
			tl = unique(filter(lambda x: x, tl))
			tags = "," + ",".join(tl)
		try:
			capkpi.db.sql(
				"update `tab%s` set _user_tags=%s where name=%s" % (self.dt, "%s", "%s"), (tags, dn)
			)
			doc = capkpi.get_doc(self.dt, dn)
			update_tags(doc, tags)
		except Exception as e:
			if capkpi.db.is_column_missing(e):
				if not tags:
					# no tags, nothing to do
					return

				self.setup()
				self.update(dn, tl)
			else:
				raise

	def setup(self):
		"""adds the _user_tags column if not exists"""
		from capkpi.database.schema import add_column

		add_column(self.dt, "_user_tags", "Data")


def delete_tags_for_document(doc):
	"""
	Delete the Tag Link entry of a document that has
	been deleted
	:param doc: Deleted document
	"""
	if not capkpi.db.table_exists("Tag Link"):
		return

	capkpi.db.sql(
		"""DELETE FROM `tabTag Link` WHERE `document_type`=%s AND `document_name`=%s""",
		(doc.doctype, doc.name),
	)


def update_tags(doc, tags):
	"""Adds tags for documents

	:param doc: Document to be added to global tags
	"""

	new_tags = list(set([tag.strip() for tag in tags.split(",") if tag]))
	existing_tags = [
		tag.tag
		for tag in capkpi.get_list(
			"Tag Link", filters={"document_type": doc.doctype, "document_name": doc.name}, fields=["tag"]
		)
	]

	added_tags = set(new_tags) - set(existing_tags)
	for tag in added_tags:
		capkpi.get_doc(
			{
				"doctype": "Tag Link",
				"document_type": doc.doctype,
				"document_name": doc.name,
				"parenttype": doc.doctype,
				"parent": doc.name,
				"title": doc.get_title() or "",
				"tag": tag,
			}
		).insert(ignore_permissions=True)

	deleted_tags = list(set(existing_tags) - set(new_tags))
	for tag in deleted_tags:
		capkpi.db.delete(
			"Tag Link", {"document_type": doc.doctype, "document_name": doc.name, "tag": tag}
		)


@capkpi.whitelist()
def get_documents_for_tag(tag):
	"""
	Search for given text in Tag Link
	:param tag: tag to be searched
	"""
	# remove hastag `#` from tag
	tag = tag[1:]
	results = []

	result = capkpi.get_list(
		"Tag Link", filters={"tag": tag}, fields=["document_type", "document_name", "title", "tag"]
	)

	for res in result:
		results.append({"doctype": res.document_type, "name": res.document_name, "content": res.title})

	return results


@capkpi.whitelist()
def get_tags_list_for_awesomebar():
	return [t.name for t in capkpi.get_list("Tag")]