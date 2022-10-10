from __future__ import unicode_literals

import capkpi


def execute():
	capkpi.reload_doc("workflow", "doctype", "workflow_transition")
	capkpi.db.sql("update `tabWorkflow Transition` set allow_self_approval=1")
