from __future__ import unicode_literals

"""
    Modify the Integer 10 Digits Value to BigInt 20 Digit value
    to generate long Naming Series

"""
import capkpi


def execute():
	capkpi.db.sql(""" ALTER TABLE `tabSeries` MODIFY current BIGINT """)
