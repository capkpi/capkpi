# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import unittest

import capkpi
import capkpi.utils
from capkpi.test_runner import make_test_objects
from capkpi.utils.goal import get_monthly_goal_graph_data, get_monthly_results


class TestGoal(unittest.TestCase):
	def setUp(self):
		make_test_objects("Event", reset=True)

	def tearDown(self):
		capkpi.db.sql("delete from `tabEvent`")
		# make_test_objects('Event', reset=True)
		capkpi.db.commit()

	def test_get_monthly_results(self):
		"""Test monthly aggregation values of a field"""
		result_dict = get_monthly_results(
			"Event", "subject", "creation", "event_type='Private'", "count"
		)

		from capkpi.utils import formatdate, today

		self.assertEqual(result_dict.get(formatdate(today(), "MM-yyyy")), 2)

	def test_get_monthly_goal_graph_data(self):
		"""Test for accurate values in graph data (based on test_get_monthly_results)"""
		docname = capkpi.get_list("Event", filters={"subject": ["=", "_Test Event 1"]})[0]["name"]
		capkpi.db.set_value("Event", docname, "description", 1)
		data = get_monthly_goal_graph_data(
			"Test",
			"Event",
			docname,
			"description",
			"description",
			"description",
			"Event",
			"",
			"description",
			"creation",
			"starts_on = '2014-01-01'",
			"count",
		)
		self.assertEqual(float(data["data"]["datasets"][0]["values"][-1]), 1)
