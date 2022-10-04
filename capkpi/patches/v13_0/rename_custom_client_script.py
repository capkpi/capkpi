import capkpi
from capkpi.model.rename_doc import rename_doc


def execute():
	if capkpi.db.exists("DocType", "Client Script"):
		return

	capkpi.flags.ignore_route_conflict_validation = True
	rename_doc("DocType", "Custom Script", "Client Script")
	capkpi.flags.ignore_route_conflict_validation = False

	capkpi.reload_doctype("Client Script", force=True)
