import capkpi


def execute():
	capkpi.reload_doctype("Translation")
	capkpi.db.sql(
		"UPDATE `tabTranslation` SET `translated_text`=`target_name`, `source_text`=`source_name`, `contributed`=0"
	)
