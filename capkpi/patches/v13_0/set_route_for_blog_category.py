import capkpi


def execute():
	categories = capkpi.get_list("Blog Category")
	for category in categories:
		doc = capkpi.get_doc("Blog Category", category["name"])
		doc.set_route()
		doc.save()
