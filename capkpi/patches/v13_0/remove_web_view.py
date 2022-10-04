import capkpi


def execute():
	capkpi.delete_doc_if_exists("DocType", "Web View")
	capkpi.delete_doc_if_exists("DocType", "Web View Component")
	capkpi.delete_doc_if_exists("DocType", "CSS Class")
