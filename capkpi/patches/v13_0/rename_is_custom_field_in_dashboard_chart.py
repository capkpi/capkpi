import capkpi
from capkpi.model.utils.rename_field import rename_field


def execute():
	if not capkpi.db.table_exists("Dashboard Chart"):
		return

	capkpi.reload_doc("desk", "doctype", "dashboard_chart")

	if capkpi.db.has_column("Dashboard Chart", "is_custom"):
		rename_field("Dashboard Chart", "is_custom", "use_report_chart")
