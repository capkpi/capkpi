import capkpi


def execute():
	capkpi.reload_doc("website", "doctype", "web_page_view", force=True)
	capkpi.db.sql("""UPDATE `tabWeb Page View` set path='/' where path=''""")
