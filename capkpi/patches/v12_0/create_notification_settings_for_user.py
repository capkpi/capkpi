from __future__ import unicode_literals

import capkpi
from capkpi.desk.doctype.notification_settings.notification_settings import (
	create_notification_settings,
)


def execute():
	capkpi.reload_doc("desk", "doctype", "notification_settings")
	capkpi.reload_doc("desk", "doctype", "notification_subscribed_document")

	users = capkpi.db.get_all("User", fields=["name"])
	for user in users:
		create_notification_settings(user.name)
