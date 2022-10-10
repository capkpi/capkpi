# -*- coding: utf-8 -*-
# Copyright (c) 2021, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi

# import capkpi
from capkpi.model.document import Document


class UserGroup(Document):
	def after_insert(self):
		capkpi.cache().delete_key("user_groups")

	def on_trash(self):
		capkpi.cache().delete_key("user_groups")
