# Copyright (c) 2021, CapKPI Technologies and Contributors
# See license.txt

import unittest

import capkpi


class TestFeedback(unittest.TestCase):
	def tearDown(self):
		capkpi.form_dict.reference_doctype = None
		capkpi.form_dict.reference_name = None
		capkpi.form_dict.rating = None
		capkpi.form_dict.feedback = None
		capkpi.local.request_ip = None

	def test_feedback_creation_updation(self):
		from capkpi.website.doctype.blog_post.test_blog_post import make_test_blog

		test_blog = make_test_blog()

		capkpi.db.sql("delete from `tabFeedback` where reference_doctype = 'Blog Post'")

		from capkpi.templates.includes.feedback.feedback import add_feedback, update_feedback

		capkpi.form_dict.reference_doctype = "Blog Post"
		capkpi.form_dict.reference_name = test_blog.name
		capkpi.form_dict.rating = 5
		capkpi.form_dict.feedback = "New feedback"
		capkpi.local.request_ip = "127.0.0.1"

		feedback = add_feedback()

		self.assertEqual(feedback.feedback, "New feedback")
		self.assertEqual(feedback.rating, 5)

		updated_feedback = update_feedback("Blog Post", test_blog.name, 6, "Updated feedback")

		self.assertEqual(updated_feedback.feedback, "Updated feedback")
		self.assertEqual(updated_feedback.rating, 6)

		capkpi.db.sql("delete from `tabFeedback` where reference_doctype = 'Blog Post'")

		test_blog.delete()
