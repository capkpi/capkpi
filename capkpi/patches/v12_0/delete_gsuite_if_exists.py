import capkpi


def execute():
	"""
	Remove GSuite Template and GSuite Settings
	"""
	capkpi.delete_doc_if_exists("DocType", "GSuite Settings")
	capkpi.delete_doc_if_exists("DocType", "GSuite Templates")
