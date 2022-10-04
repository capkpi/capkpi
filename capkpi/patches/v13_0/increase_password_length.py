import capkpi


def execute():
	capkpi.db.change_column_type(table="__Auth", column="password", type="TEXT")
