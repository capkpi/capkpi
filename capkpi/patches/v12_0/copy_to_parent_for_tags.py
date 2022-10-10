import capkpi


def execute():

	capkpi.db.sql("UPDATE `tabTag Link` SET parenttype=document_type")
	capkpi.db.sql("UPDATE `tabTag Link` SET parent=document_name")
