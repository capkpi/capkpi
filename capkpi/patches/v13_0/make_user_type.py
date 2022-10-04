import capkpi
from capkpi.utils.install import create_user_type


def execute():
	capkpi.reload_doc("core", "doctype", "role")
	capkpi.reload_doc("core", "doctype", "user_document_type")
	capkpi.reload_doc("core", "doctype", "user_type_module")
	capkpi.reload_doc("core", "doctype", "user_select_document_type")
	capkpi.reload_doc("core", "doctype", "user_type")

	create_user_type()
