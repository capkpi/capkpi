import capkpi
from capkpi.desk.utils import slug


def execute():
	for doctype in capkpi.get_all("DocType", ["name", "route"], dict(istable=0)):
		if not doctype.route:
			capkpi.db.set_value("DocType", doctype.name, "route", slug(doctype.name), update_modified=False)
