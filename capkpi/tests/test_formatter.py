# -*- coding: utf-8 -*-
import unittest

import capkpi
from capkpi import format


class TestFormatter(unittest.TestCase):
	def test_currency_formatting(self):
		df = capkpi._dict({"fieldname": "amount", "fieldtype": "Currency", "options": "currency"})

		doc = capkpi._dict({"amount": 5})
		capkpi.db.set_default("currency", "INR")

		# if currency field is not passed then default currency should be used.
		self.assertEqual(format(100000, df, doc, format="#,###.##"), "₹ 100,000.00")

		doc.currency = "USD"
		self.assertEqual(format(100000, df, doc, format="#,###.##"), "$ 100,000.00")

		capkpi.db.set_default("currency", None)
