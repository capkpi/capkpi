# -*- coding: utf-8 -*-
# Copyright (c) 2019, CapKPI Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import json
import unittest

import capkpi


class TestComment(unittest.TestCase):
	def test_comment_creation(self):
		test_doc = capkpi.get_doc(dict(doctype="ToDo", description="test"))
		test_doc.insert()
		comment = test_doc.add_comment("Comment", "test comment")

		test_doc.reload()

		# check if updated in _comments cache
		comments = json.loads(test_doc.get("_comments"))
		self.assertEqual(comments[0].get("name"), comment.name)
		self.assertEqual(comments[0].get("comment"), comment.content)

		# check document creation
		comment_1 = capkpi.get_all(
			"Comment",
			fields=["*"],
			filters=dict(reference_doctype=test_doc.doctype, reference_name=test_doc.name),
		)[0]

		self.assertEqual(comment_1.content, "test comment")

	# test via blog
	def test_public_comment(self):
		from capkpi.website.doctype.blog_post.test_blog_post import make_test_blog

		test_blog = make_test_blog()

		capkpi.db.sql("delete from `tabComment` where reference_doctype = 'Blog Post'")

		from capkpi.templates.includes.comments.comments import add_comment

		add_comment(
			"Good comment with 10 chars",
			"test@test.com",
			"Good Tester",
			"Blog Post",
			test_blog.name,
			test_blog.route,
		)

		self.assertEqual(
			capkpi.get_all(
				"Comment",
				fields=["*"],
				filters=dict(reference_doctype=test_blog.doctype, reference_name=test_blog.name),
			)[0].published,
			1,
		)

		capkpi.db.sql("delete from `tabComment` where reference_doctype = 'Blog Post'")

		add_comment(
			"pleez vizits my site http://mysite.com",
			"test@test.com",
			"bad commentor",
			"Blog Post",
			test_blog.name,
			test_blog.route,
		)

		self.assertEqual(
			len(
				capkpi.get_all(
					"Comment",
					fields=["*"],
					filters=dict(reference_doctype=test_blog.doctype, reference_name=test_blog.name),
				)
			),
			0,
		)

		test_blog.delete()
