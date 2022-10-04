# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import os

import capkpi
from capkpi.core.doctype.data_import.data_import import export_json, import_doc


def sync_fixtures(app=None):
	"""Import, overwrite fixtures from `[app]/fixtures`"""
	if app:
		apps = [app]
	else:
		apps = capkpi.get_installed_apps()

	capkpi.flags.in_fixtures = True

	for app in apps:
		fixtures_path = capkpi.get_app_path(app, "fixtures")
		if os.path.exists(fixtures_path):
			import_doc(fixtures_path)

		import_custom_scripts(app)

	capkpi.flags.in_fixtures = False

	capkpi.db.commit()


def import_custom_scripts(app):
	"""Import custom scripts from `[app]/fixtures/custom_scripts`"""
	if os.path.exists(capkpi.get_app_path(app, "fixtures", "custom_scripts")):
		for fname in os.listdir(capkpi.get_app_path(app, "fixtures", "custom_scripts")):
			if fname.endswith(".js"):
				with open(capkpi.get_app_path(app, "fixtures", "custom_scripts") + os.path.sep + fname) as f:
					doctype = fname.rsplit(".", 1)[0]
					script = f.read()
					if capkpi.db.exists("Client Script", {"dt": doctype}):
						custom_script = capkpi.get_doc("Client Script", {"dt": doctype})
						custom_script.script = script
						custom_script.save()
					else:
						capkpi.get_doc({"doctype": "Client Script", "dt": doctype, "script": script}).insert()


def export_fixtures(app=None):
	"""Export fixtures as JSON to `[app]/fixtures`"""
	if app:
		apps = [app]
	else:
		apps = capkpi.get_installed_apps()
	for app in apps:
		for fixture in capkpi.get_hooks("fixtures", app_name=app):
			filters = None
			or_filters = None
			if isinstance(fixture, dict):
				filters = fixture.get("filters")
				or_filters = fixture.get("or_filters")
				fixture = fixture.get("doctype") or fixture.get("dt")
			print(
				"Exporting {0} app {1} filters {2}".format(fixture, app, (filters if filters else or_filters))
			)
			if not os.path.exists(capkpi.get_app_path(app, "fixtures")):
				os.mkdir(capkpi.get_app_path(app, "fixtures"))

			export_json(
				fixture,
				capkpi.get_app_path(app, "fixtures", capkpi.scrub(fixture) + ".json"),
				filters=filters,
				or_filters=or_filters,
				order_by="idx asc, creation asc",
			)
