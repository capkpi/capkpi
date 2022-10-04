from __future__ import unicode_literals

import unittest

import capkpi
import capkpi.website.render
from capkpi.utils import set_request
from capkpi.website.router import resolve_route

test_records = capkpi.get_test_records("Web Page")


def get_page_content(route):
	set_request(method="GET", path=route)
	response = capkpi.website.render.render()
	return capkpi.as_unicode(response.data)


class TestWebPage(unittest.TestCase):
	def setUp(self):
		capkpi.db.sql("delete from `tabWeb Page`")
		for t in test_records:
			capkpi.get_doc(t).insert()

	def test_check_sitemap(self):
		resolve_route("test-web-page-1")
		resolve_route("test-web-page-1/test-web-page-2")
		resolve_route("test-web-page-1/test-web-page-3")

	def test_base_template(self):
		content = get_page_content("/_test/_test_custom_base.html")

		# assert the text in base template is rendered
		self.assertTrue("<h1>This is for testing</h1>" in capkpi.as_unicode(content))

		# assert template block rendered
		self.assertTrue("<p>Test content</p>" in capkpi.as_unicode(content))

	def test_content_type(self):
		web_page = capkpi.get_doc(
			dict(
				doctype="Web Page",
				title="Test Content Type",
				published=1,
				content_type="Rich Text",
				main_section="rich text",
				main_section_md="# h1\nmarkdown content",
				main_section_html="<div>html content</div>",
			)
		).insert()

		self.assertTrue("rich text" in get_page_content("/test-content-type"))

		web_page.content_type = "Markdown"
		web_page.save()
		self.assertTrue("markdown content" in get_page_content("/test-content-type"))

		web_page.content_type = "HTML"
		web_page.save()
		self.assertTrue("html content" in get_page_content("/test-content-type"))

		web_page.delete()

	def test_dynamic_route(self):
		web_page = capkpi.get_doc(
			dict(
				doctype="Web Page",
				title="Test Dynamic Route",
				published=1,
				dynamic_route=1,
				route="/doctype-view/<doctype>",
				content_type="HTML",
				dymamic_template=1,
				main_section_html="<div>{{ capkpi.form_dict.doctype }}</div>",
			)
		).insert()

		try:
			content = get_page_content("/doctype-view/DocField")
			self.assertTrue("<div>DocField</div>" in content)
		finally:
			web_page.delete()
