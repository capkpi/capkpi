from __future__ import unicode_literals

import capkpi
from capkpi.model.rename_doc import rename_doc


def execute():
	if capkpi.db.table_exists("Workflow Action") and not capkpi.db.table_exists(
		"Workflow Action Master"
	):
		rename_doc("DocType", "Workflow Action", "Workflow Action Master")
		capkpi.reload_doc("workflow", "doctype", "workflow_action_master")
