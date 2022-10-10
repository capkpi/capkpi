# Copyright (c) 2021, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See LICENSE
"""
	capkpi.coverage
	~~~~~~~~~~~~~~~~

	Coverage settings for capkpi
"""

STANDARD_INCLUSIONS = ["*.py"]

STANDARD_EXCLUSIONS = [
	"*.js",
	"*.xml",
	"*.pyc",
	"*.css",
	"*.less",
	"*.scss",
	"*.vue",
	"*.html",
	"*/test_*",
	"*/node_modules/*",
	"*/doctype/*/*_dashboard.py",
	"*/patches/*",
]

CAPKPI_EXCLUSIONS = [
	"*/tests/*",
	"*/commands/*",
	"*/capkpi/change_log/*",
	"*/capkpi/exceptions*",
	"*capkpi/setup.py",
	"*/doctype/*/*_dashboard.py",
	"*/patches/*",
]
