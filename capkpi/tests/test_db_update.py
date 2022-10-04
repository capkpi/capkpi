import unittest

import capkpi
from capkpi.core.utils import find
from capkpi.custom.doctype.property_setter.property_setter import make_property_setter
from capkpi.utils import cstr


class TestDBUpdate(unittest.TestCase):
	def test_db_update(self):
		doctype = "User"
		capkpi.reload_doctype("User", force=True)
		capkpi.model.meta.trim_tables("User")
		make_property_setter(doctype, "bio", "fieldtype", "Text", "Data")
		make_property_setter(doctype, "middle_name", "fieldtype", "Data", "Text")
		make_property_setter(doctype, "enabled", "default", "1", "Int")

		capkpi.db.updatedb(doctype)

		field_defs = get_field_defs(doctype)
		table_columns = capkpi.db.get_table_columns_description("tab{}".format(doctype))

		self.assertEqual(len(field_defs), len(table_columns))

		for field_def in field_defs:
			fieldname = field_def.get("fieldname")
			table_column = find(table_columns, lambda d: d.get("name") == fieldname)

			fieldtype = get_fieldtype_from_def(field_def)

			fallback_default = (
				"0" if field_def.get("fieldtype") in capkpi.model.numeric_fieldtypes else "NULL"
			)
			default = field_def.default if field_def.default is not None else fallback_default

			self.assertEqual(fieldtype, table_column.type)
			self.assertIn(cstr(table_column.default) or "NULL", [cstr(default), "'{}'".format(default)])

	def test_index_and_unique_constraints(self):
		doctype = "User"
		capkpi.reload_doctype("User", force=True)
		capkpi.model.meta.trim_tables("User")

		make_property_setter(doctype, "middle_name", "unique", "1", "Check")
		capkpi.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertTrue(middle_name_in_table.unique)

		make_property_setter(doctype, "middle_name", "unique", "0", "Check")
		capkpi.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertFalse(middle_name_in_table.unique)

		make_property_setter(doctype, "middle_name", "search_index", "1", "Check")
		capkpi.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertTrue(middle_name_in_table.index)

		make_property_setter(doctype, "middle_name", "search_index", "0", "Check")
		capkpi.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertFalse(middle_name_in_table.index)

		make_property_setter(doctype, "middle_name", "search_index", "1", "Check")
		make_property_setter(doctype, "middle_name", "unique", "1", "Check")
		capkpi.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertTrue(middle_name_in_table.index)
		self.assertTrue(middle_name_in_table.unique)

		make_property_setter(doctype, "middle_name", "search_index", "1", "Check")
		make_property_setter(doctype, "middle_name", "unique", "0", "Check")
		capkpi.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertTrue(middle_name_in_table.index)
		self.assertFalse(middle_name_in_table.unique)

		make_property_setter(doctype, "middle_name", "search_index", "0", "Check")
		make_property_setter(doctype, "middle_name", "unique", "1", "Check")
		capkpi.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertFalse(middle_name_in_table.index)
		self.assertTrue(middle_name_in_table.unique)

		# explicitly make a text index
		capkpi.db.add_index(doctype, ["email_signature(200)"])
		capkpi.db.updatedb(doctype)
		email_sig_column = get_table_column("User", "email_signature")
		self.assertEqual(email_sig_column.index, 1)


def get_fieldtype_from_def(field_def):
	fieldtuple = capkpi.db.type_map.get(field_def.fieldtype, ("", 0))
	fieldtype = fieldtuple[0]
	if fieldtype in ("varchar", "datetime", "int"):
		fieldtype += "({})".format(field_def.length or fieldtuple[1])
	return fieldtype


def get_field_defs(doctype):
	meta = capkpi.get_meta(doctype, cached=False)
	field_defs = meta.get_fieldnames_with_value(True)
	field_defs += get_other_fields_meta(meta)
	return field_defs


def get_other_fields_meta(meta):
	default_fields_map = {
		"name": ("Data", 0),
		"owner": ("Data", 0),
		"parent": ("Data", 0),
		"parentfield": ("Data", 0),
		"modified_by": ("Data", 0),
		"parenttype": ("Data", 0),
		"creation": ("Datetime", 0),
		"modified": ("Datetime", 0),
		"idx": ("Int", 8),
		"docstatus": ("Check", 0),
	}

	optional_fields = capkpi.db.OPTIONAL_COLUMNS
	if meta.track_seen:
		optional_fields.append("_seen")

	optional_fields_map = {field: ("Text", 0) for field in optional_fields}
	fields = dict(default_fields_map, **optional_fields_map)
	field_map = [
		capkpi._dict({"fieldname": field, "fieldtype": _type, "length": _length})
		for field, (_type, _length) in fields.items()
	]

	return field_map


def get_table_column(doctype, fieldname):
	table_columns = capkpi.db.get_table_columns_description("tab{}".format(doctype))
	return find(table_columns, lambda d: d.get("name") == fieldname)
