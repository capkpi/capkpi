# -*- coding: utf-8 -*-
# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi.model.document import Document


class UnhandledEmail(Document):
	pass


def remove_old_unhandled_emails():
	capkpi.db.sql(
		"""DELETE FROM `tabUnhandled Email`
	WHERE creation < %s""",
		capkpi.utils.add_days(capkpi.utils.nowdate(), -30),
	)
