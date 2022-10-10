# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

from math import ceil

import capkpi
from capkpi import _
from capkpi.utils import (
	cint,
	get_fullname,
	global_date_format,
	markdown,
	sanitize_html,
	strip_html_tags,
	today,
)
from capkpi.website.render import clear_cache
from capkpi.website.utils import find_first_image, get_comment_list, get_html_content_based_on_type
from capkpi.website.website_generator import WebsiteGenerator


class BlogPost(WebsiteGenerator):
	website = capkpi._dict(route="blog", order_by="published_on desc")

	@capkpi.whitelist()
	def make_route(self):
		if not self.route:
			return (
				capkpi.db.get_value("Blog Category", self.blog_category, "route")
				+ "/"
				+ self.scrub(self.title)
			)

	def get_feed(self):
		return self.title

	def validate(self):
		super(BlogPost, self).validate()

		if not self.blog_intro:
			content = get_html_content_based_on_type(self, "content", self.content_type)
			self.blog_intro = content[:200]
			self.blog_intro = strip_html_tags(self.blog_intro)

		if self.blog_intro:
			self.blog_intro = self.blog_intro[:200]

		if not self.meta_title:
			self.meta_title = self.title[:60]
		else:
			self.meta_title = self.meta_title[:60]

		if not self.meta_description:
			self.meta_description = self.blog_intro[:140]
		else:
			self.meta_description = self.meta_description[:140]

		if self.published and not self.published_on:
			self.published_on = today()

		if self.featured:
			if not self.meta_image:
				capkpi.throw(_("A featured post must have a cover image"))
			self.reset_featured_for_other_blogs()

		self.set_read_time()

	def reset_featured_for_other_blogs(self):
		all_posts = capkpi.get_all("Blog Post", {"featured": 1})
		for post in all_posts:
			capkpi.db.set_value("Blog Post", post.name, "featured", 0)

	def on_update(self):
		super(BlogPost, self).on_update()
		clear_cache("writers")

	def on_trash(self):
		super(BlogPost, self).on_trash()

	def get_context(self, context):
		# this is for double precaution. usually it wont reach this code if not published
		if not cint(self.published):
			raise Exception("This blog has not been published yet!")

		context.no_breadcrumbs = True

		# temp fields
		context.full_name = get_fullname(self.owner)
		context.updated = global_date_format(self.published_on)
		context.social_links = self.fetch_social_links_info()
		context.cta = self.fetch_cta()
		context.enable_cta = not self.hide_cta and capkpi.db.get_single_value(
			"Blog Settings", "show_cta_in_blog", cache=True
		)

		if self.blogger:
			context.blogger_info = capkpi.get_doc("Blogger", self.blogger).as_dict()
			context.author = self.blogger

		context.content = get_html_content_based_on_type(self, "content", self.content_type)

		# if meta description is not present, then blog intro or first 140 characters of the blog will be set as description
		context.description = (
			self.meta_description or self.blog_intro or strip_html_tags(context.content[:140])
		)

		context.metatags = {
			"name": self.meta_title,
			"description": context.description,
		}

		# if meta image is not present, then first image inside the blog will be set as the meta image
		image = find_first_image(context.content)
		context.metatags["image"] = self.meta_image or image or None

		self.load_comments(context)
		self.load_feedback(context)

		context.category = capkpi.db.get_value(
			"Blog Category", context.doc.blog_category, ["title", "route"], as_dict=1
		)
		context.parents = [
			{"name": _("Home"), "route": "/"},
			{"name": "Blog", "route": "/blog"},
			{"label": context.category.title, "route": context.category.route},
		]
		context.guest_allowed = True

	def fetch_cta(self):
		if capkpi.db.get_single_value("Blog Settings", "show_cta_in_blog", cache=True):
			blog_settings = capkpi.get_cached_doc("Blog Settings")

			return {
				"show_cta_in_blog": 1,
				"title": blog_settings.title,
				"subtitle": blog_settings.subtitle,
				"cta_label": blog_settings.cta_label,
				"cta_url": blog_settings.cta_url,
			}

		return {}

	def fetch_social_links_info(self):
		if not capkpi.db.get_single_value("Blog Settings", "enable_social_sharing", cache=True):
			return []

		url = capkpi.local.site + "/" + self.route

		social_links = [
			{
				"icon": "twitter",
				"link": "https://twitter.com/intent/tweet?text=" + self.title + "&url=" + url,
			},
			{"icon": "facebook", "link": "https://www.facebook.com/sharer.php?u=" + url},
			{"icon": "linkedin", "link": "https://www.linkedin.com/sharing/share-offsite/?url=" + url},
			{"icon": "envelope", "link": "mailto:?subject=" + self.title + "&body=" + url},
		]

		return social_links

	def load_comments(self, context):
		context.comment_list = get_comment_list(self.doctype, self.name)

		if not context.comment_list:
			context.comment_text = _("No comments yet")
		else:
			if (len(context.comment_list)) == 1:
				context.comment_text = _("1 comment")
			else:
				context.comment_text = _("{0} comments").format(len(context.comment_list))

	def load_feedback(self, context):
		user = capkpi.session.user
		if user == "Guest":
			user = ""
		feedback = capkpi.get_all(
			"Feedback",
			fields=["feedback", "rating"],
			filters=dict(reference_doctype=self.doctype, reference_name=self.name, owner=user),
		)
		context.user_feedback = feedback[0] if feedback else ""

	def set_read_time(self):
		content = self.content or self.content_html or ""
		if self.content_type == "Markdown":
			content = markdown(self.content_md)

		total_words = len(strip_html_tags(content).split())
		self.read_time = ceil(total_words / 250)


def get_list_context(context=None):
	list_context = capkpi._dict(
		get_list=get_blog_list,
		no_breadcrumbs=True,
		hide_filters=True,
		children=get_children(),
		# show_search = True,
		title=_("Blog"),
	)

	category = capkpi.utils.escape_html(
		capkpi.local.form_dict.blog_category or capkpi.local.form_dict.category
	)
	if category:
		category_title = get_blog_category(category)
		list_context.sub_title = _("Posts filed under {0}").format(category_title)
		list_context.title = category_title

	elif capkpi.local.form_dict.blogger:
		blogger = capkpi.db.get_value("Blogger", {"name": capkpi.local.form_dict.blogger}, "full_name")
		list_context.sub_title = _("Posts by {0}").format(blogger)
		list_context.title = blogger

	elif capkpi.local.form_dict.txt:
		list_context.sub_title = _('Filtered by "{0}"').format(sanitize_html(capkpi.local.form_dict.txt))

	if list_context.sub_title:
		list_context.parents = [{"name": _("Home"), "route": "/"}, {"name": "Blog", "route": "/blog"}]
	else:
		list_context.parents = [{"name": _("Home"), "route": "/"}]

	list_context.update(capkpi.get_doc("Blog Settings").as_dict(no_default_fields=True))

	return list_context


def get_children():
	return capkpi.db.sql(
		"""select route as name,
		title from `tabBlog Category`
		where published = 1
		and exists (select name from `tabBlog Post`
			where `tabBlog Post`.blog_category=`tabBlog Category`.name and published=1)
		order by title asc""",
		as_dict=1,
	)


def clear_blog_cache():
	for blog in capkpi.db.sql_list(
		"""select route from
		`tabBlog Post` where ifnull(published,0)=1"""
	):
		clear_cache(blog)

	clear_cache("writers")


def get_blog_category(route):
	return capkpi.db.get_value("Blog Category", {"name": route}, "title") or route


def get_blog_list(
	doctype, txt=None, filters=None, limit_start=0, limit_page_length=20, order_by=None
):
	conditions = []
	category = filters.blog_category or capkpi.utils.escape_html(
		capkpi.local.form_dict.blog_category or capkpi.local.form_dict.category
	)
	if filters:
		if filters.blogger:
			conditions.append("t1.blogger=%s" % capkpi.db.escape(filters.blogger))
	if category:
		conditions.append("t1.blog_category=%s" % capkpi.db.escape(category))

	if txt:
		conditions.append(
			'(t1.content like {0} or t1.title like {0}")'.format(capkpi.db.escape("%" + txt + "%"))
		)

	if conditions:
		capkpi.local.no_cache = 1

	query = """\
		select
			t1.title, t1.name, t1.blog_category, t1.route, t1.published_on, t1.read_time,
				t1.published_on as creation,
				t1.read_time as read_time,
				t1.featured as featured,
				t1.meta_image as cover_image,
				t1.content as content,
				t1.content_type as content_type,
				t1.content_html as content_html,
				t1.content_md as content_md,
				ifnull(t1.blog_intro, t1.content) as intro,
				t2.full_name, t2.avatar, t1.blogger,
				(select count(name) from `tabComment`
					where
						comment_type='Comment'
						and reference_doctype='Blog Post'
						and reference_name=t1.name) as comments
		from `tabBlog Post` t1, `tabBlogger` t2
		where ifnull(t1.published,0)=1
		and t1.blogger = t2.name
		%(condition)s
		order by featured desc, published_on desc, name asc
		limit %(page_len)s OFFSET %(start)s""" % {
		"start": limit_start,
		"page_len": limit_page_length,
		"condition": (" and " + " and ".join(conditions)) if conditions else "",
	}

	posts = capkpi.db.sql(query, as_dict=1)

	for post in posts:
		post.content = get_html_content_based_on_type(post, "content", post.content_type)
		if not post.cover_image:
			post.cover_image = find_first_image(post.content)
		post.published = global_date_format(post.creation)
		post.content = strip_html_tags(post.content)

		if not post.comments:
			post.comment_text = _("No comments yet")
		elif post.comments == 1:
			post.comment_text = _("1 comment")
		else:
			post.comment_text = _("{0} comments").format(str(post.comments))

		post.avatar = post.avatar or ""
		post.category = capkpi.db.get_value(
			"Blog Category", post.blog_category, ["name", "route", "title"], as_dict=True
		)

		if (
			post.avatar
			and (not "http:" in post.avatar and not "https:" in post.avatar)
			and not post.avatar.startswith("/")
		):
			post.avatar = "/" + post.avatar

	return posts