import capkpi


def execute():
	"""
	Deprecate Feedback Trigger and Rating. This feature was not customizable.
	Now can be achieved via custom Web Forms
	"""
	capkpi.delete_doc("DocType", "Feedback Trigger")
	capkpi.delete_doc("DocType", "Feedback Rating")
