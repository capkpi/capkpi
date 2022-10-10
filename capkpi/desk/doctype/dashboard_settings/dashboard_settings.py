# -*- coding: utf-8 -*-
# Copyright (c) 2020, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json

import capkpi

# import capkpi
from capkpi.model.document import Document


class DashboardSettings(Document):
	pass


@capkpi.whitelist()
def create_dashboard_settings(user):
	if not capkpi.db.exists("Dashboard Settings", user):
		doc = capkpi.new_doc("Dashboard Settings")
		doc.name = user
		doc.insert(ignore_permissions=True)
		capkpi.db.commit()
		return doc


def get_permission_query_conditions(user):
	if not user:
		user = capkpi.session.user

	return """(`tabDashboard Settings`.name = {user})""".format(user=capkpi.db.escape(user))


@capkpi.whitelist()
def save_chart_config(reset, config, chart_name):
	reset = capkpi.parse_json(reset)
	doc = capkpi.get_doc("Dashboard Settings", capkpi.session.user)
	chart_config = capkpi.parse_json(doc.chart_config) or {}

	if reset:
		chart_config[chart_name] = {}
	else:
		config = capkpi.parse_json(config)
		if not chart_name in chart_config:
			chart_config[chart_name] = {}
		chart_config[chart_name].update(config)

	capkpi.db.set_value(
		"Dashboard Settings", capkpi.session.user, "chart_config", json.dumps(chart_config)
	)
