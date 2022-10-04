import capkpi


def execute():
	providers = capkpi.get_all("Social Login Key")

	for provider in providers:
		doc = capkpi.get_doc("Social Login Key", provider)
		doc.set_icon()
		doc.save()
