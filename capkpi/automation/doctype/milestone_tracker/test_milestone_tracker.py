# -*- coding: utf-8 -*-
# Copyright (c) 2019, CapKPI Technologies and Contributors
# See license.txt
from __future__ import unicode_literals

import unittest

import capkpi
import capkpi.cache_manager


class TestMilestoneTracker(unittest.TestCase):
	def test_milestone(self):
		capkpi.db.sql("delete from `tabMilestone Tracker`")

		capkpi.cache().delete_key("milestone_tracker_map")

		milestone_tracker = capkpi.get_doc(
			dict(doctype="Milestone Tracker", document_type="ToDo", track_field="status")
		).insert()

		todo = capkpi.get_doc(dict(doctype="ToDo", description="test milestone", status="Open")).insert()

		milestones = capkpi.get_all(
			"Milestone",
			fields=["track_field", "value", "milestone_tracker"],
			filters=dict(reference_type=todo.doctype, reference_name=todo.name),
		)

		self.assertEqual(len(milestones), 1)
		self.assertEqual(milestones[0].track_field, "status")
		self.assertEqual(milestones[0].value, "Open")

		todo.status = "Closed"
		todo.save()

		milestones = capkpi.get_all(
			"Milestone",
			fields=["track_field", "value", "milestone_tracker"],
			filters=dict(reference_type=todo.doctype, reference_name=todo.name),
			order_by="modified desc",
		)

		self.assertEqual(len(milestones), 2)
		self.assertEqual(milestones[0].track_field, "status")
		self.assertEqual(milestones[0].value, "Closed")

		# cleanup
		capkpi.db.sql("delete from tabMilestone")
		milestone_tracker.delete()
