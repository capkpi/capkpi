import capkpi
from capkpi.desk.page.setup_wizard.install_fixtures import update_global_search_doctypes


def execute():
	capkpi.reload_doc("desk", "doctype", "global_search_doctype")
	capkpi.reload_doc("desk", "doctype", "global_search_settings")
	update_global_search_doctypes()
