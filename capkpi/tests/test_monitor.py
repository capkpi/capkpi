#  -*- coding: utf-8 -*-
# Copyright (c) 2020, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import unittest

import capkpi
import capkpi.monitor
from capkpi.monitor import MONITOR_REDIS_KEY
from capkpi.utils import set_request
from capkpi.utils.response import build_response


class TestMonitor(unittest.TestCase):
	def setUp(self):
		capkpi.conf.monitor = 1
		capkpi.cache().delete_value(MONITOR_REDIS_KEY)

	def test_enable_monitor(self):
		set_request(method="GET", path="/api/method/capkpi.ping")
		response = build_response("json")

		capkpi.monitor.start()
		capkpi.monitor.stop(response)

		logs = capkpi.cache().lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)

		log = capkpi.parse_json(logs[0].decode())
		self.assertTrue(log.duration)
		self.assertTrue(log.site)
		self.assertTrue(log.timestamp)
		self.assertTrue(log.uuid)
		self.assertTrue(log.request)
		self.assertEqual(log.transaction_type, "request")
		self.assertEqual(log.request["method"], "GET")

	def test_job(self):
		capkpi.utils.background_jobs.execute_job(
			capkpi.local.site, "capkpi.ping", None, None, {}, is_async=False
		)

		logs = capkpi.cache().lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)
		log = capkpi.parse_json(logs[0].decode())
		self.assertEqual(log.transaction_type, "job")
		self.assertTrue(log.job)
		self.assertEqual(log.job["method"], "capkpi.ping")
		self.assertEqual(log.job["scheduled"], False)
		self.assertEqual(log.job["wait"], 0)

	def test_flush(self):
		set_request(method="GET", path="/api/method/capkpi.ping")
		response = build_response("json")
		capkpi.monitor.start()
		capkpi.monitor.stop(response)

		open(capkpi.monitor.log_file(), "w").close()
		capkpi.monitor.flush()

		with open(capkpi.monitor.log_file()) as f:
			logs = f.readlines()

		self.assertEqual(len(logs), 1)
		log = capkpi.parse_json(logs[0])
		self.assertEqual(log.transaction_type, "request")

	def tearDown(self):
		capkpi.conf.monitor = 0
		capkpi.cache().delete_value(MONITOR_REDIS_KEY)
