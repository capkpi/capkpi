import capkpi


def execute():
	web_pages = capkpi.get_all("Web Page", ["name", "description"])

	for web_page in web_pages:
		if web_page.description and web_page.route:
			doc = capkpi.new_doc("Website Route Meta")
			doc.name = web_page.route
			doc.append("meta_tags", {"key": "description", "value": web_page.description})
			doc.save()
