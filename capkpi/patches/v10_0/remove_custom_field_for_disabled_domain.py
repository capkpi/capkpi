from __future__ import unicode_literals

import capkpi


def execute():
	capkpi.reload_doc("core", "doctype", "domain")
	capkpi.reload_doc("core", "doctype", "has_domain")
	active_domains = capkpi.get_active_domains()
	all_domains = capkpi.get_all("Domain")

	for d in all_domains:
		if d.name not in active_domains:
			inactive_domain = capkpi.get_doc("Domain", d.name)
			inactive_domain.setup_data()
			inactive_domain.remove_custom_field()
