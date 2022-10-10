# -*- coding: utf-8 -*-
# Copyright (c) 2019, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi.model.document import Document


class CommunicationLink(Document):
	pass


def on_doctype_update():
	capkpi.db.add_index("Communication Link", ["link_doctype", "link_name"])
