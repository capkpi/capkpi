import capkpi


def execute():
	for name in ("desktop", "space"):
		capkpi.delete_doc("Page", name)
