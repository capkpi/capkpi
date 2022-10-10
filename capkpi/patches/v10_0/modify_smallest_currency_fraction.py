# Copyright (c) 2018, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import capkpi


def execute():
	capkpi.db.set_value("Currency", "USD", "smallest_currency_fraction_value", "0.01")
