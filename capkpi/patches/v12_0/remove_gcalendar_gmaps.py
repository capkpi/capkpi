import capkpi


def execute():
	"""
	Remove GCalendar and GCalendar Settings
	Remove Google Maps Settings as its been merged with Delivery Trips
	"""
	capkpi.delete_doc_if_exists("DocType", "GCalendar Account")
	capkpi.delete_doc_if_exists("DocType", "GCalendar Settings")
	capkpi.delete_doc_if_exists("DocType", "Google Maps Settings")
