from __future__ import unicode_literals

import capkpi
from capkpi.utils.password import LegacyPassword


def execute():
	all_auths = capkpi.db.sql(
		"""SELECT `name`, `password`, `salt` FROM `__Auth`
		WHERE doctype='User' AND `fieldname`='password'""",
		as_dict=True,
	)

	for auth in all_auths:
		if auth.salt and auth.salt != "":
			pwd = LegacyPassword.hash(auth.password, salt=auth.salt.encode("UTF-8"))
			capkpi.db.sql(
				"""UPDATE `__Auth` SET `password`=%(pwd)s, `salt`=NULL
				WHERE `doctype`='User' AND `fieldname`='password' AND `name`=%(user)s""",
				{"pwd": pwd, "user": auth.name},
			)

	capkpi.reload_doctype("User")

	capkpi.db.sql_ddl("""ALTER TABLE `__Auth` DROP COLUMN `salt`""")
