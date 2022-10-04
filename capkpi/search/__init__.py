# Copyright (c) 2020, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import capkpi
from capkpi.search.full_text_search import FullTextSearch
from capkpi.search.website_search import WebsiteSearch
from capkpi.utils import cint


@capkpi.whitelist(allow_guest=True)
def web_search(query, scope=None, limit=20):
	limit = cint(limit)
	ws = WebsiteSearch(index_name="web_routes")
	return ws.search(query, scope, limit)
