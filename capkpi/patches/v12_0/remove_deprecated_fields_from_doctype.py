import capkpi


def execute():
	capkpi.reload_doc("core", "doctype", "doctype_link")
	capkpi.reload_doc("core", "doctype", "doctype_action")
	capkpi.reload_doc("core", "doctype", "doctype")
	capkpi.model.delete_fields(
		{"DocType": ["hide_heading", "image_view", "read_only_onload"]}, delete=1
	)

	capkpi.db.sql(
		"""
		DELETE from `tabProperty Setter`
		WHERE property = 'read_only_onload'
	"""
	)
