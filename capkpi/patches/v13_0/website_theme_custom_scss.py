import capkpi


def execute():
	capkpi.reload_doc("website", "doctype", "website_theme_ignore_app")
	capkpi.reload_doc("website", "doctype", "color")
	capkpi.reload_doc("website", "doctype", "website_theme", force=True)

	for theme in capkpi.get_all("Website Theme"):
		doc = capkpi.get_doc("Website Theme", theme.name)
		if not doc.get("custom_scss") and doc.theme_scss:
			# move old theme to new theme
			doc.custom_scss = doc.theme_scss

			if doc.background_color:
				setup_color_record(doc.background_color)

			doc.save()


def setup_color_record(color):
	capkpi.get_doc(
		{
			"doctype": "Color",
			"__newname": color,
			"color": color,
		}
	).save()
