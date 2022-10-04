# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

"""Use blog post test to test user permissions logic"""

import unittest

import capkpi
import capkpi.defaults
import capkpi.model.meta
from capkpi.core.doctype.user_permission.user_permission import clear_user_permissions
from capkpi.core.page.permission_manager.permission_manager import reset, update
from capkpi.desk.form.load import getdoc
from capkpi.permissions import (
	add_permission,
	add_user_permission,
	clear_user_permissions_for_doctype,
	get_doc_permissions,
	remove_user_permission,
	update_permission_property,
)
from capkpi.test_runner import make_test_records_for_doctype

test_dependencies = ["Blogger", "Blog Post", "User", "Contact", "Salutation"]


class TestPermissions(unittest.TestCase):
	def setUp(self):
		capkpi.clear_cache(doctype="Blog Post")

		if not capkpi.flags.permission_user_setup_done:
			user = capkpi.get_doc("User", "test1@example.com")
			user.add_roles("Website Manager")
			user.add_roles("System Manager")

			user = capkpi.get_doc("User", "test2@example.com")
			user.add_roles("Blogger")

			user = capkpi.get_doc("User", "test3@example.com")
			user.add_roles("Sales User")

			user = capkpi.get_doc("User", "testperm@example.com")
			user.add_roles("Website Manager")

			capkpi.flags.permission_user_setup_done = True

		reset("Blogger")
		reset("Blog Post")

		capkpi.db.sql("delete from `tabUser Permission`")

		capkpi.set_user("test1@example.com")

	def tearDown(self):
		capkpi.set_user("Administrator")
		capkpi.db.set_value("Blogger", "_Test Blogger 1", "user", None)

		clear_user_permissions_for_doctype("Blog Category")
		clear_user_permissions_for_doctype("Blog Post")
		clear_user_permissions_for_doctype("Blogger")

	@staticmethod
	def set_strict_user_permissions(ignore):
		ss = capkpi.get_doc("System Settings")
		ss.apply_strict_user_permissions = ignore
		ss.flags.ignore_mandatory = 1
		ss.save()

	def test_basic_permission(self):
		post = capkpi.get_doc("Blog Post", "-test-blog-post")
		self.assertTrue(post.has_permission("read"))

	def test_select_permission(self):
		# grant only select perm to blog post
		add_permission("Blog Post", "Sales User", 0)
		update_permission_property("Blog Post", "Sales User", 0, "select", 1)
		update_permission_property("Blog Post", "Sales User", 0, "read", 0)
		update_permission_property("Blog Post", "Sales User", 0, "write", 0)

		capkpi.clear_cache(doctype="Blog Post")
		capkpi.set_user("test3@example.com")

		# validate select perm
		post = capkpi.get_doc("Blog Post", "-test-blog-post")
		self.assertTrue(post.has_permission("select"))

		# validate does not have read and write perm
		self.assertFalse(post.has_permission("read"))
		self.assertRaises(capkpi.PermissionError, post.save)

	def test_user_permissions_in_doc(self):
		add_user_permission("Blog Category", "-test-blog-category-1", "test2@example.com")

		capkpi.set_user("test2@example.com")

		post = capkpi.get_doc("Blog Post", "-test-blog-post")
		self.assertFalse(post.has_permission("read"))
		self.assertFalse(get_doc_permissions(post).get("read"))

		post1 = capkpi.get_doc("Blog Post", "-test-blog-post-1")
		self.assertTrue(post1.has_permission("read"))
		self.assertTrue(get_doc_permissions(post1).get("read"))

	def test_user_permissions_in_report(self):
		add_user_permission("Blog Category", "-test-blog-category-1", "test2@example.com")

		capkpi.set_user("test2@example.com")
		names = [d.name for d in capkpi.get_list("Blog Post", fields=["name", "blog_category"])]

		self.assertTrue("-test-blog-post-1" in names)
		self.assertFalse("-test-blog-post" in names)

	def test_default_values(self):
		doc = capkpi.new_doc("Blog Post")
		self.assertFalse(doc.get("blog_category"))

		# Fetch default based on single user permission
		add_user_permission("Blog Category", "-test-blog-category-1", "test2@example.com")

		capkpi.set_user("test2@example.com")
		doc = capkpi.new_doc("Blog Post")
		self.assertEqual(doc.get("blog_category"), "-test-blog-category-1")

		# Don't fetch default if user permissions is more than 1
		add_user_permission(
			"Blog Category", "-test-blog-category", "test2@example.com", ignore_permissions=True
		)
		capkpi.clear_cache()
		doc = capkpi.new_doc("Blog Post")
		self.assertFalse(doc.get("blog_category"))

		# Fetch user permission set as default from multiple user permission
		add_user_permission(
			"Blog Category",
			"-test-blog-category-2",
			"test2@example.com",
			ignore_permissions=True,
			is_default=1,
		)
		capkpi.clear_cache()
		doc = capkpi.new_doc("Blog Post")
		self.assertEqual(doc.get("blog_category"), "-test-blog-category-2")

	def test_user_link_match_doc(self):
		blogger = capkpi.get_doc("Blogger", "_Test Blogger 1")
		blogger.user = "test2@example.com"
		blogger.save()

		capkpi.set_user("test2@example.com")

		post = capkpi.get_doc("Blog Post", "-test-blog-post-2")
		self.assertTrue(post.has_permission("read"))

		post1 = capkpi.get_doc("Blog Post", "-test-blog-post-1")
		self.assertFalse(post1.has_permission("read"))

	def test_user_link_match_report(self):
		blogger = capkpi.get_doc("Blogger", "_Test Blogger 1")
		blogger.user = "test2@example.com"
		blogger.save()

		capkpi.set_user("test2@example.com")

		names = [d.name for d in capkpi.get_list("Blog Post", fields=["name", "owner"])]
		self.assertTrue("-test-blog-post-2" in names)
		self.assertFalse("-test-blog-post-1" in names)

	def test_set_user_permissions(self):
		capkpi.set_user("test1@example.com")
		add_user_permission("Blog Post", "-test-blog-post", "test2@example.com")

	def test_not_allowed_to_set_user_permissions(self):
		capkpi.set_user("test2@example.com")

		# this user can't add user permissions
		self.assertRaises(
			capkpi.PermissionError, add_user_permission, "Blog Post", "-test-blog-post", "test2@example.com"
		)

	def test_read_if_explicit_user_permissions_are_set(self):
		self.test_set_user_permissions()

		capkpi.set_user("test2@example.com")

		# user can only access permitted blog post
		doc = capkpi.get_doc("Blog Post", "-test-blog-post")
		self.assertTrue(doc.has_permission("read"))

		# and not this one
		doc = capkpi.get_doc("Blog Post", "-test-blog-post-1")
		self.assertFalse(doc.has_permission("read"))

	def test_not_allowed_to_remove_user_permissions(self):
		self.test_set_user_permissions()

		capkpi.set_user("test2@example.com")

		# user cannot remove their own user permissions
		self.assertRaises(
			capkpi.PermissionError,
			remove_user_permission,
			"Blog Post",
			"-test-blog-post",
			"test2@example.com",
		)

	def test_user_permissions_if_applied_on_doc_being_evaluated(self):
		capkpi.set_user("test2@example.com")
		doc = capkpi.get_doc("Blog Post", "-test-blog-post-1")
		self.assertTrue(doc.has_permission("read"))

		capkpi.set_user("test1@example.com")
		add_user_permission("Blog Post", "-test-blog-post", "test2@example.com")

		capkpi.set_user("test2@example.com")
		doc = capkpi.get_doc("Blog Post", "-test-blog-post-1")
		self.assertFalse(doc.has_permission("read"))

		doc = capkpi.get_doc("Blog Post", "-test-blog-post")
		self.assertTrue(doc.has_permission("read"))

	def test_set_only_once(self):
		blog_post = capkpi.get_meta("Blog Post")
		doc = capkpi.get_doc("Blog Post", "-test-blog-post-1")
		doc.db_set("title", "Old")
		blog_post.get_field("title").set_only_once = 1
		doc.title = "New"
		self.assertRaises(capkpi.CannotChangeConstantError, doc.save)
		blog_post.get_field("title").set_only_once = 0

	def test_set_only_once_child_table_rows(self):
		doctype_meta = capkpi.get_meta("DocType")
		doctype_meta.get_field("fields").set_only_once = 1
		doc = capkpi.get_doc("DocType", "Blog Post")

		# remove last one
		doc.fields = doc.fields[:-1]
		self.assertRaises(capkpi.CannotChangeConstantError, doc.save)
		capkpi.clear_cache(doctype="DocType")

	def test_set_only_once_child_table_row_value(self):
		doctype_meta = capkpi.get_meta("DocType")
		doctype_meta.get_field("fields").set_only_once = 1
		doc = capkpi.get_doc("DocType", "Blog Post")

		# change one property from the child table
		doc.fields[-1].fieldtype = "Check"
		self.assertRaises(capkpi.CannotChangeConstantError, doc.save)
		capkpi.clear_cache(doctype="DocType")

	def test_set_only_once_child_table_okay(self):
		doctype_meta = capkpi.get_meta("DocType")
		doctype_meta.get_field("fields").set_only_once = 1
		doc = capkpi.get_doc("DocType", "Blog Post")

		doc.load_doc_before_save()
		self.assertFalse(doc.validate_set_only_once())
		capkpi.clear_cache(doctype="DocType")

	def test_user_permission_doctypes(self):
		add_user_permission("Blog Category", "-test-blog-category-1", "test2@example.com")
		add_user_permission("Blogger", "_Test Blogger 1", "test2@example.com")

		capkpi.set_user("test2@example.com")

		capkpi.clear_cache(doctype="Blog Post")

		doc = capkpi.get_doc("Blog Post", "-test-blog-post")
		self.assertFalse(doc.has_permission("read"))

		doc = capkpi.get_doc("Blog Post", "-test-blog-post-2")
		self.assertTrue(doc.has_permission("read"))

		capkpi.clear_cache(doctype="Blog Post")

	def if_owner_setup(self):
		update("Blog Post", "Blogger", 0, "if_owner", 1)

		add_user_permission("Blog Category", "-test-blog-category-1", "test2@example.com")
		add_user_permission("Blogger", "_Test Blogger 1", "test2@example.com")

		capkpi.clear_cache(doctype="Blog Post")

	def test_insert_if_owner_with_user_permissions(self):
		"""If `If Owner` is checked for a Role, check if that document
		is allowed to be read, updated, submitted, etc. except be created,
		even if the document is restricted based on User Permissions."""
		capkpi.delete_doc("Blog Post", "-test-blog-post-title")

		self.if_owner_setup()

		capkpi.set_user("test2@example.com")

		doc = capkpi.get_doc(
			{
				"doctype": "Blog Post",
				"blog_category": "-test-blog-category",
				"blogger": "_Test Blogger 1",
				"title": "_Test Blog Post Title",
				"content": "_Test Blog Post Content",
			}
		)

		self.assertRaises(capkpi.PermissionError, doc.insert)

		capkpi.set_user("test1@example.com")
		add_user_permission("Blog Category", "-test-blog-category", "test2@example.com")

		capkpi.set_user("test2@example.com")
		doc.insert()

		capkpi.set_user("Administrator")
		remove_user_permission("Blog Category", "-test-blog-category", "test2@example.com")

		capkpi.set_user("test2@example.com")
		doc = capkpi.get_doc(doc.doctype, doc.name)
		self.assertTrue(doc.has_permission("read"))
		self.assertTrue(doc.has_permission("write"))
		self.assertFalse(doc.has_permission("create"))

		# delete created record
		capkpi.set_user("Administrator")
		capkpi.delete_doc("Blog Post", "-test-blog-post-title")

	def test_ignore_user_permissions_if_missing(self):
		"""If there are no user permissions, then allow as per role"""

		add_user_permission("Blog Category", "-test-blog-category", "test2@example.com")
		capkpi.set_user("test2@example.com")

		doc = capkpi.get_doc(
			{
				"doctype": "Blog Post",
				"blog_category": "-test-blog-category-2",
				"blogger": "_Test Blogger 1",
				"title": "_Test Blog Post Title",
				"content": "_Test Blog Post Content",
			}
		)

		self.assertFalse(doc.has_permission("write"))

		capkpi.set_user("Administrator")
		remove_user_permission("Blog Category", "-test-blog-category", "test2@example.com")

		capkpi.set_user("test2@example.com")
		self.assertTrue(doc.has_permission("write"))

	def test_strict_user_permissions(self):
		"""If `Strict User Permissions` is checked in System Settings,
		show records even if User Permissions are missing for a linked
		doctype"""

		capkpi.set_user("Administrator")
		capkpi.db.sql("DELETE FROM `tabContact`")
		capkpi.db.sql("DELETE FROM `tabContact Email`")
		capkpi.db.sql("DELETE FROM `tabContact Phone`")

		reset("Salutation")
		reset("Contact")

		make_test_records_for_doctype("Contact", force=True)

		add_user_permission("Salutation", "Mr", "test3@example.com")
		self.set_strict_user_permissions(0)

		allowed_contact = capkpi.get_doc("Contact", "_Test Contact For _Test Customer")
		other_contact = capkpi.get_doc("Contact", "_Test Contact For _Test Supplier")

		capkpi.set_user("test3@example.com")
		self.assertTrue(allowed_contact.has_permission("read"))
		self.assertTrue(other_contact.has_permission("read"))
		self.assertEqual(len(capkpi.get_list("Contact")), 2)

		capkpi.set_user("Administrator")
		self.set_strict_user_permissions(1)

		capkpi.set_user("test3@example.com")
		self.assertTrue(allowed_contact.has_permission("read"))
		self.assertFalse(other_contact.has_permission("read"))
		self.assertTrue(len(capkpi.get_list("Contact")), 1)

		capkpi.set_user("Administrator")
		self.set_strict_user_permissions(0)

		clear_user_permissions_for_doctype("Salutation")
		clear_user_permissions_for_doctype("Contact")

	def test_user_permissions_not_applied_if_user_can_edit_user_permissions(self):
		add_user_permission("Blogger", "_Test Blogger 1", "test1@example.com")

		# test1@example.com has rights to create user permissions
		# so it should not matter if explicit user permissions are not set
		self.assertTrue(capkpi.get_doc("Blogger", "_Test Blogger").has_permission("read"))

	def test_user_permission_is_not_applied_if_user_roles_does_not_have_permission(self):
		add_user_permission("Blog Post", "-test-blog-post-1", "test3@example.com")
		capkpi.set_user("test3@example.com")
		doc = capkpi.get_doc("Blog Post", "-test-blog-post-1")
		self.assertFalse(doc.has_permission("read"))

		capkpi.set_user("Administrator")
		user = capkpi.get_doc("User", "test3@example.com")
		user.add_roles("Blogger")
		capkpi.set_user("test3@example.com")
		self.assertTrue(doc.has_permission("read"))

		capkpi.set_user("Administrator")
		user.remove_roles("Blogger")

	def test_contextual_user_permission(self):
		# should be applicable for across all doctypes
		add_user_permission("Blogger", "_Test Blogger", "test2@example.com")
		# should be applicable only while accessing Blog Post
		add_user_permission(
			"Blogger", "_Test Blogger 1", "test2@example.com", applicable_for="Blog Post"
		)
		# should be applicable only while accessing User
		add_user_permission("Blogger", "_Test Blogger 2", "test2@example.com", applicable_for="User")

		posts = capkpi.get_all("Blog Post", fields=["name", "blogger"])

		# Get all posts for admin
		self.assertEqual(len(posts), 4)

		capkpi.set_user("test2@example.com")

		posts = capkpi.get_list("Blog Post", fields=["name", "blogger"])

		# Should get only posts with allowed blogger via user permission
		# only '_Test Blogger', '_Test Blogger 1' are allowed in Blog Post
		self.assertEqual(len(posts), 3)

		for post in posts:
			self.assertIn(
				post.blogger,
				["_Test Blogger", "_Test Blogger 1"],
				"A post from {} is not expected.".format(post.blogger),
			)

	def test_if_owner_permission_overrides_properly(self):
		# check if user is not granted access if the user is not the owner of the doc
		# Blogger has only read access on the blog post unless he is the owner of the blog
		update("Blog Post", "Blogger", 0, "if_owner", 1)
		update("Blog Post", "Blogger", 0, "read", 1)
		update("Blog Post", "Blogger", 0, "write", 1)
		update("Blog Post", "Blogger", 0, "delete", 1)

		# currently test2 user has not created any document
		# still he should be able to do get_list query which should
		# not raise permission error but simply return empty list
		capkpi.set_user("test2@example.com")
		self.assertEqual(capkpi.get_list("Blog Post"), [])

		capkpi.set_user("Administrator")

		# creates a custom docperm with just read access
		# now any user can read any blog post (but other rights are limited to the blog post owner)
		add_permission("Blog Post", "Blogger")
		capkpi.clear_cache(doctype="Blog Post")

		capkpi.delete_doc("Blog Post", "-test-blog-post-title")

		capkpi.set_user("test1@example.com")

		doc = capkpi.get_doc(
			{
				"doctype": "Blog Post",
				"blog_category": "-test-blog-category",
				"blogger": "_Test Blogger 1",
				"title": "_Test Blog Post Title",
				"content": "_Test Blog Post Content",
			}
		)

		doc.insert()

		capkpi.set_user("test2@example.com")
		doc = capkpi.get_doc(doc.doctype, doc.name)

		self.assertTrue(doc.has_permission("read"))
		self.assertFalse(doc.has_permission("write"))
		self.assertFalse(doc.has_permission("delete"))

		# check if owner of the doc has the access that is available only for the owner of the doc
		capkpi.set_user("test1@example.com")
		doc = capkpi.get_doc(doc.doctype, doc.name)

		self.assertTrue(doc.has_permission("read"))
		self.assertTrue(doc.has_permission("write"))
		self.assertTrue(doc.has_permission("delete"))

		# delete the created doc
		capkpi.delete_doc("Blog Post", "-test-blog-post-title")

	def test_if_owner_permission_on_getdoc(self):
		update("Blog Post", "Blogger", 0, "if_owner", 1)
		update("Blog Post", "Blogger", 0, "read", 1)
		update("Blog Post", "Blogger", 0, "write", 1)
		update("Blog Post", "Blogger", 0, "delete", 1)
		capkpi.clear_cache(doctype="Blog Post")

		capkpi.set_user("test1@example.com")

		doc = capkpi.get_doc(
			{
				"doctype": "Blog Post",
				"blog_category": "-test-blog-category",
				"blogger": "_Test Blogger 1",
				"title": "_Test Blog Post Title New",
				"content": "_Test Blog Post Content",
			}
		)

		doc.insert()

		getdoc("Blog Post", doc.name)
		doclist = [d.name for d in capkpi.response.docs]
		self.assertTrue(doc.name in doclist)

		capkpi.set_user("test2@example.com")
		self.assertRaises(capkpi.PermissionError, getdoc, "Blog Post", doc.name)

	def test_if_owner_permission_on_get_list(self):
		doc = capkpi.get_doc(
			{
				"doctype": "Blog Post",
				"blog_category": "-test-blog-category",
				"blogger": "_Test Blogger 1",
				"title": "_Test If Owner Permissions on Get List",
				"content": "_Test Blog Post Content",
			}
		)

		doc.insert(ignore_if_duplicate=True)

		update("Blog Post", "Blogger", 0, "if_owner", 1)
		update("Blog Post", "Blogger", 0, "read", 1)
		user = capkpi.get_doc("User", "test2@example.com")
		user.add_roles("Website Manager")
		capkpi.clear_cache(doctype="Blog Post")

		capkpi.set_user("test2@example.com")
		self.assertIn(doc.name, capkpi.get_list("Blog Post", pluck="name"))

		# Become system manager to remove role
		capkpi.set_user("test1@example.com")
		user.remove_roles("Website Manager")
		capkpi.clear_cache(doctype="Blog Post")

		capkpi.set_user("test2@example.com")
		self.assertNotIn(doc.name, capkpi.get_list("Blog Post", pluck="name"))

	def test_if_owner_permission_on_delete(self):
		update("Blog Post", "Blogger", 0, "if_owner", 1)
		update("Blog Post", "Blogger", 0, "read", 1)
		update("Blog Post", "Blogger", 0, "write", 1)
		update("Blog Post", "Blogger", 0, "delete", 1)

		# Remove delete perm
		update("Blog Post", "Website Manager", 0, "delete", 0)

		capkpi.clear_cache(doctype="Blog Post")

		capkpi.set_user("test2@example.com")

		doc = capkpi.get_doc(
			{
				"doctype": "Blog Post",
				"blog_category": "-test-blog-category",
				"blogger": "_Test Blogger 1",
				"title": "_Test Blog Post Title New 1",
				"content": "_Test Blog Post Content",
			}
		)

		doc.insert()

		getdoc("Blog Post", doc.name)
		doclist = [d.name for d in capkpi.response.docs]
		self.assertTrue(doc.name in doclist)

		capkpi.set_user("testperm@example.com")

		# Website Manager able to read
		getdoc("Blog Post", doc.name)
		doclist = [d.name for d in capkpi.response.docs]
		self.assertTrue(doc.name in doclist)

		# Website Manager should not be able to delete
		self.assertRaises(capkpi.PermissionError, capkpi.delete_doc, "Blog Post", doc.name)

		capkpi.set_user("test2@example.com")
		capkpi.delete_doc("Blog Post", "-test-blog-post-title-new-1")
		update("Blog Post", "Website Manager", 0, "delete", 1)

	def test_clear_user_permissions(self):
		current_user = capkpi.session.user
		capkpi.set_user("Administrator")
		clear_user_permissions_for_doctype("Blog Category", "test2@example.com")
		clear_user_permissions_for_doctype("Blog Post", "test2@example.com")

		add_user_permission("Blog Post", "-test-blog-post-1", "test2@example.com")
		add_user_permission("Blog Post", "-test-blog-post-2", "test2@example.com")
		add_user_permission("Blog Category", "-test-blog-category-1", "test2@example.com")

		deleted_user_permission_count = clear_user_permissions("test2@example.com", "Blog Post")

		self.assertEqual(deleted_user_permission_count, 2)

		blog_post_user_permission_count = capkpi.db.count(
			"User Permission", filters={"user": "test2@example.com", "allow": "Blog Post"}
		)

		self.assertEqual(blog_post_user_permission_count, 0)

		blog_category_user_permission_count = capkpi.db.count(
			"User Permission", filters={"user": "test2@example.com", "allow": "Blog Category"}
		)

		self.assertEqual(blog_category_user_permission_count, 1)

		# reset the user
		capkpi.set_user(current_user)
