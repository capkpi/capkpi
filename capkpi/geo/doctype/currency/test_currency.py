# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# License: See license.txt

# pre loaded

from __future__ import unicode_literals

import capkpi
from capkpi.tests.utils import CapKPITestCase


class TestUser(CapKPITestCase):
	def test_default_currency_on_setup(self):
		usd = capkpi.get_doc("Currency", "USD")
		self.assertTrue(usd.enabled)
		self.assertEqual(usd.fraction, "Cent")
