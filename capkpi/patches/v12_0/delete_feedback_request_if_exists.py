import capkpi


def execute():
	capkpi.db.sql(
		"""
        DELETE from `tabDocType`
        WHERE name = 'Feedback Request'
    """
	)
