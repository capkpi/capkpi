# -*- coding: utf-8 -*-
# Copyright (c) 2015, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi.model.document import Document


class PortalSettings(Document):
	def add_item(self, item):
		"""insert new portal menu item if route is not set, or role is different"""
		exists = [d for d in self.get("menu", []) if d.get("route") == item.get("route")]
		if exists and item.get("role"):
			if exists[0].role != item.get("role"):
				exists[0].role = item.get("role")
				return True
		elif not exists:
			item["enabled"] = 1
			self.append("menu", item)
			return True

	@capkpi.whitelist()
	def reset(self):
		"""Restore defaults"""
		self.menu = []
		self.sync_menu()

	def sync_menu(self):
		"""Sync portal menu items"""
		dirty = False
		for item in capkpi.get_hooks("standard_portal_menu_items"):
			if item.get("role") and not capkpi.db.exists("Role", item.get("role")):
				capkpi.get_doc({"doctype": "Role", "role_name": item.get("role"), "desk_access": 0}).insert()
			if self.add_item(item):
				dirty = True

		if dirty:
			self.save()

	def on_update(self):
		self.clear_cache()

	def clear_cache(self):
		# make js and css
		# clear web cache (for menus!)
		capkpi.clear_cache(user="Guest")

		from capkpi.website.render import clear_cache

		clear_cache()

		# clears role based home pages
		capkpi.clear_cache()