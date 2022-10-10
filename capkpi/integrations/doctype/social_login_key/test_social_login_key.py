# -*- coding: utf-8 -*-
# Copyright (c) 2017, CapKPI Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import unittest

import capkpi
from capkpi.integrations.doctype.social_login_key.social_login_key import BaseUrlNotSetError


class TestSocialLoginKey(unittest.TestCase):
	def test_adding_capkpi_social_login_provider(self):
		provider_name = "CapKPI"
		social_login_key = make_social_login_key(social_login_provider=provider_name)
		social_login_key.get_social_login_provider(provider_name, initialize=True)
		self.assertRaises(BaseUrlNotSetError, social_login_key.insert)


def make_social_login_key(**kwargs):
	kwargs["doctype"] = "Social Login Key"
	if not "provider_name" in kwargs:
		kwargs["provider_name"] = "Test OAuth2 Provider"
	doc = capkpi.get_doc(kwargs)
	return doc


def create_or_update_social_login_key():
	# used in other tests (connected app, oauth20)
	try:
		social_login_key = capkpi.get_doc("Social Login Key", "capkpi")
	except capkpi.DoesNotExistError:
		social_login_key = capkpi.new_doc("Social Login Key")
	social_login_key.get_social_login_provider("CapKPI", initialize=True)
	social_login_key.base_url = capkpi.utils.get_url()
	social_login_key.enable_social_login = 0
	social_login_key.save()
	capkpi.db.commit()

	return social_login_key
