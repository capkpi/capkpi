import click

import capkpi


def execute():
	capkpi.delete_doc_if_exists("DocType", "Chat Message")
	capkpi.delete_doc_if_exists("DocType", "Chat Message Attachment")
	capkpi.delete_doc_if_exists("DocType", "Chat Profile")
	capkpi.delete_doc_if_exists("DocType", "Chat Token")
	capkpi.delete_doc_if_exists("DocType", "Chat Room User")
	capkpi.delete_doc_if_exists("DocType", "Chat Room")
	capkpi.delete_doc_if_exists("Module Def", "Chat")

	click.secho(
		"Chat Module is moved to a separate app and is removed from CapKPI in version-13.\n"
		"Please install the app to continue using the chat feature: https://github.com/capkpi/chat",
		fg="yellow",
	)
