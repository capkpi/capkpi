import capkpi


def execute():
	doctype = "Top Bar Item"
	if not capkpi.db.table_exists(doctype) or not capkpi.db.has_column(doctype, "target"):
		return

	capkpi.reload_doc("website", "doctype", "top_bar_item")
	capkpi.db.set_value(doctype, {"target": 'target = "_blank"'}, "open_in_new_tab", 1)
