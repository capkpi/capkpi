# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi
import capkpi.defaults
from capkpi import _
from capkpi.core.doctype.doctype.doctype import (
	clear_permissions_cache,
	validate_permissions_for_doctype,
)
from capkpi.modules.import_file import get_file_path, read_doc_from_file
from capkpi.permissions import (
	add_permission,
	get_all_perms,
	get_linked_doctypes,
	reset_perms,
	setup_custom_perms,
	update_permission_property,
)
from capkpi.translate import send_translations
from capkpi.utils.user import get_users_with_role as _get_user_with_role

not_allowed_in_permission_manager = ["DocType", "Patch Log", "Module Def", "Transaction Log"]


@capkpi.whitelist()
def get_roles_and_doctypes():
	capkpi.only_for("System Manager")
	send_translations(capkpi.get_lang_dict("doctype", "DocPerm"))

	active_domains = capkpi.get_active_domains()

	doctypes = capkpi.get_all(
		"DocType",
		filters={
			"istable": 0,
			"name": ("not in", ",".join(not_allowed_in_permission_manager)),
		},
		or_filters={"ifnull(restrict_to_domain, '')": "", "restrict_to_domain": ("in", active_domains)},
		fields=["name"],
	)

	restricted_roles = ["Administrator"]
	if capkpi.session.user != "Administrator":
		custom_user_type_roles = capkpi.get_all("User Type", filters={"is_standard": 0}, fields=["role"])
		for row in custom_user_type_roles:
			restricted_roles.append(row.role)

		restricted_roles.append("All")

	roles = capkpi.get_all(
		"Role",
		filters={
			"name": ("not in", restricted_roles),
			"disabled": 0,
		},
		or_filters={"ifnull(restrict_to_domain, '')": "", "restrict_to_domain": ("in", active_domains)},
		fields=["name"],
	)

	doctypes_list = [{"label": _(d.get("name")), "value": d.get("name")} for d in doctypes]
	roles_list = [{"label": _(d.get("name")), "value": d.get("name")} for d in roles]

	return {
		"doctypes": sorted(doctypes_list, key=lambda d: d["label"]),
		"roles": sorted(roles_list, key=lambda d: d["label"]),
	}


@capkpi.whitelist()
def get_permissions(doctype=None, role=None):
	capkpi.only_for("System Manager")
	if role:
		out = get_all_perms(role)
		if doctype:
			out = [p for p in out if p.parent == doctype]
	else:
		filters = dict(parent=doctype)
		if capkpi.session.user != "Administrator":
			custom_roles = capkpi.get_all("Role", filters={"is_custom": 1})
			filters["role"] = ["not in", [row.name for row in custom_roles]]

		out = capkpi.get_all("Custom DocPerm", fields="*", filters=filters, order_by="permlevel")
		if not out:
			out = capkpi.get_all("DocPerm", fields="*", filters=filters, order_by="permlevel")

	linked_doctypes = {}
	for d in out:
		if not d.parent in linked_doctypes:
			linked_doctypes[d.parent] = get_linked_doctypes(d.parent)
		d.linked_doctypes = linked_doctypes[d.parent]
		meta = capkpi.get_meta(d.parent)
		if meta:
			d.is_submittable = meta.is_submittable
			d.in_create = meta.in_create

	return out


@capkpi.whitelist()
def add(parent, role, permlevel):
	capkpi.only_for("System Manager")
	add_permission(parent, role, permlevel)


@capkpi.whitelist()
def update(doctype, role, permlevel, ptype, value=None):
	"""Update role permission params

	Args:
	    doctype (str): Name of the DocType to update params for
	    role (str): Role to be updated for, eg "Website Manager".
	    permlevel (int): perm level the provided rule applies to
	    ptype (str): permission type, example "read", "delete", etc.
	    value (None, optional): value for ptype, None indicates False

	Returns:
	    str: Refresh flag is permission is updated successfully
	"""
	capkpi.only_for("System Manager")
	out = update_permission_property(doctype, role, permlevel, ptype, value)
	return "refresh" if out else None


@capkpi.whitelist()
def remove(doctype, role, permlevel):
	capkpi.only_for("System Manager")
	setup_custom_perms(doctype)

	name = capkpi.get_value("Custom DocPerm", dict(parent=doctype, role=role, permlevel=permlevel))

	capkpi.db.sql("delete from `tabCustom DocPerm` where name=%s", name)
	if not capkpi.get_all("Custom DocPerm", dict(parent=doctype)):
		capkpi.throw(_("There must be atleast one permission rule."), title=_("Cannot Remove"))

	validate_permissions_for_doctype(doctype, for_remove=True, alert=True)


@capkpi.whitelist()
def reset(doctype):
	capkpi.only_for("System Manager")
	reset_perms(doctype)
	clear_permissions_cache(doctype)


@capkpi.whitelist()
def get_users_with_role(role):
	capkpi.only_for("System Manager")
	return _get_user_with_role(role)


@capkpi.whitelist()
def get_standard_permissions(doctype):
	capkpi.only_for("System Manager")
	meta = capkpi.get_meta(doctype)
	if meta.custom:
		doc = capkpi.get_doc("DocType", doctype)
		return [p.as_dict() for p in doc.permissions]
	else:
		# also used to setup permissions via patch
		path = get_file_path(meta.module, "DocType", doctype)
		return read_doc_from_file(path).get("permissions")