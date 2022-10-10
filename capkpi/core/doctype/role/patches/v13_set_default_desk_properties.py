import capkpi

from ..role import desk_properties


def execute():
	capkpi.reload_doctype("user")
	capkpi.reload_doctype("role")
	for role in capkpi.get_all("Role", ["name", "desk_access"]):
		role_doc = capkpi.get_doc("Role", role.name)
		for key in desk_properties:
			role_doc.set(key, role_doc.desk_access)
		role_doc.save()
