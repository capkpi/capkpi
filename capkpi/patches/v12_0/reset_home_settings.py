import capkpi


def execute():
	capkpi.reload_doc("core", "doctype", "user")
	capkpi.db.sql(
		"""
		UPDATE `tabUser`
		SET `home_settings` = ''
		WHERE `user_type` = 'System User'
	"""
	)
