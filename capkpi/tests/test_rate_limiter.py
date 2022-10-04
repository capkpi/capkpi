#  -*- coding: utf-8 -*-

# Copyright (c) 2020, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import time
import unittest

from werkzeug.wrappers import Response

import capkpi
import capkpi.rate_limiter
from capkpi.rate_limiter import RateLimiter
from capkpi.utils import cint


class TestRateLimiter(unittest.TestCase):
	def setUp(self):
		pass

	def test_apply_with_limit(self):
		capkpi.conf.rate_limit = {"window": 86400, "limit": 1}
		capkpi.rate_limiter.apply()

		self.assertTrue(hasattr(capkpi.local, "rate_limiter"))
		self.assertIsInstance(capkpi.local.rate_limiter, RateLimiter)

		capkpi.cache().delete(capkpi.local.rate_limiter.key)
		delattr(capkpi.local, "rate_limiter")

	def test_apply_without_limit(self):
		capkpi.conf.rate_limit = None
		capkpi.rate_limiter.apply()

		self.assertFalse(hasattr(capkpi.local, "rate_limiter"))

	def test_respond_over_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		capkpi.conf.rate_limit = {"window": 86400, "limit": 0.01}
		self.assertRaises(capkpi.TooManyRequestsError, capkpi.rate_limiter.apply)
		capkpi.rate_limiter.update()

		response = capkpi.rate_limiter.respond()

		self.assertIsInstance(response, Response)
		self.assertEqual(response.status_code, 429)

		headers = capkpi.local.rate_limiter.headers()
		self.assertIn("Retry-After", headers)
		self.assertNotIn("X-RateLimit-Used", headers)
		self.assertIn("X-RateLimit-Reset", headers)
		self.assertIn("X-RateLimit-Limit", headers)
		self.assertIn("X-RateLimit-Remaining", headers)
		self.assertTrue(int(headers["X-RateLimit-Reset"]) <= 86400)
		self.assertEqual(int(headers["X-RateLimit-Limit"]), 10000)
		self.assertEqual(int(headers["X-RateLimit-Remaining"]), 0)

		capkpi.cache().delete(limiter.key)
		capkpi.cache().delete(capkpi.local.rate_limiter.key)
		delattr(capkpi.local, "rate_limiter")

	def test_respond_under_limit(self):
		capkpi.conf.rate_limit = {"window": 86400, "limit": 0.01}
		capkpi.rate_limiter.apply()
		capkpi.rate_limiter.update()
		response = capkpi.rate_limiter.respond()
		self.assertEqual(response, None)

		capkpi.cache().delete(capkpi.local.rate_limiter.key)
		delattr(capkpi.local, "rate_limiter")

	def test_headers_under_limit(self):
		capkpi.conf.rate_limit = {"window": 86400, "limit": 0.01}
		capkpi.rate_limiter.apply()
		capkpi.rate_limiter.update()
		headers = capkpi.local.rate_limiter.headers()
		self.assertNotIn("Retry-After", headers)
		self.assertIn("X-RateLimit-Reset", headers)
		self.assertTrue(int(headers["X-RateLimit-Reset"] < 86400))
		self.assertEqual(int(headers["X-RateLimit-Used"]), capkpi.local.rate_limiter.duration)
		self.assertEqual(int(headers["X-RateLimit-Limit"]), 10000)
		self.assertEqual(int(headers["X-RateLimit-Remaining"]), 10000)

		capkpi.cache().delete(capkpi.local.rate_limiter.key)
		delattr(capkpi.local, "rate_limiter")

	def test_reject_over_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		limiter = RateLimiter(0.01, 86400)
		self.assertRaises(capkpi.TooManyRequestsError, limiter.apply)

		capkpi.cache().delete(limiter.key)

	def test_do_not_reject_under_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		limiter = RateLimiter(0.02, 86400)
		self.assertEqual(limiter.apply(), None)

		capkpi.cache().delete(limiter.key)

	def test_update_method(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		self.assertEqual(limiter.duration, cint(capkpi.cache().get(limiter.key)))

		capkpi.cache().delete(limiter.key)
