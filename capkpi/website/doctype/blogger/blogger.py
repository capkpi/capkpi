# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi import _
from capkpi.model.document import Document


class Blogger(Document):
	def validate(self):
		if self.user and not capkpi.db.exists("User", self.user):
			# for data import
			capkpi.get_doc(
				{"doctype": "User", "email": self.user, "first_name": self.user.split("@")[0]}
			).insert()

	def on_update(self):
		"if user is set, then update all older blogs"

		from capkpi.website.doctype.blog_post.blog_post import clear_blog_cache

		clear_blog_cache()

		if self.user:
			for blog in capkpi.db.sql_list(
				"""select name from `tabBlog Post` where owner=%s
				and ifnull(blogger,'')=''""",
				self.user,
			):
				b = capkpi.get_doc("Blog Post", blog)
				b.blogger = self.name
				b.save()

			capkpi.permissions.add_user_permission("Blogger", self.name, self.user)