# Copyright (c) 2020, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi


def execute():
	if capkpi.db.exists("DocType", "Onboarding"):
		capkpi.rename_doc("DocType", "Onboarding", "Module Onboarding", ignore_if_exists=True)
