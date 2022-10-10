# Copyright (c) 2021, CapKPI Technologies and contributors
# For license information, please see license.txt

import capkpi
from capkpi import _
from capkpi.model.document import Document


class NetworkPrinterSettings(Document):
	@capkpi.whitelist()
	def get_printers_list(self, ip="localhost", port=631):
		printer_list = []
		try:
			import cups
		except ImportError:
			capkpi.throw(
				_(
					"""This feature can not be used as dependencies are missing.
				Please contact your system manager to enable this by installing pycups!"""
				)
			)
			return
		try:
			cups.setServer(self.server_ip)
			cups.setPort(self.port)
			conn = cups.Connection()
			printers = conn.getPrinters()
			for printer_id, printer in printers.items():
				printer_list.append({"value": printer_id, "label": printer["printer-make-and-model"]})

		except RuntimeError:
			capkpi.throw(_("Failed to connect to server"))
		except capkpi.ValidationError:
			capkpi.throw(_("Failed to connect to server"))
		return printer_list


@capkpi.whitelist()
def get_network_printer_settings():
	return capkpi.db.get_list("Network Printer Settings", pluck="name")
