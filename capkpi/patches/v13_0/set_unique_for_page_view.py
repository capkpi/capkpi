import capkpi


def execute():
	capkpi.reload_doc("website", "doctype", "web_page_view", force=True)
	site_url = capkpi.utils.get_site_url(capkpi.local.site)
	capkpi.db.sql(
		"""UPDATE `tabWeb Page View` set is_unique=1 where referrer LIKE '%{0}%'""".format(site_url)
	)
