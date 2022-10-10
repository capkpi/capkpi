# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# License: See license.txt

from __future__ import unicode_literals

import json
import os

from six import string_types
from werkzeug.useragents import UserAgent

import capkpi
from capkpi.geo.country_info import get_country_info
from capkpi.translate import get_dict, send_translations, set_default_language
from capkpi.utils import cint, strip
from capkpi.utils.password import update_password

from . import install_fixtures


def get_setup_stages(args):

	# App setup stage functions should not include capkpi.db.commit
	# That is done by capkpi after successful completion of all stages
	stages = [
		{
			"status": "Updating global settings",
			"fail_msg": "Failed to update global settings",
			"tasks": [
				{"fn": update_global_settings, "args": args, "fail_msg": "Failed to update global settings"}
			],
		}
	]

	stages += get_stages_hooks(args) + get_setup_complete_hooks(args)

	stages.append(
		{
			# post executing hooks
			"status": "Wrapping up",
			"fail_msg": "Failed to complete setup",
			"tasks": [
				{"fn": run_post_setup_complete, "args": args, "fail_msg": "Failed to complete setup"}
			],
		}
	)

	return stages


@capkpi.whitelist()
def setup_complete(args):
	"""Calls hooks for `setup_wizard_complete`, sets home page as `desktop`
	and clears cache. If wizard breaks, calls `setup_wizard_exception` hook"""

	# Setup complete: do not throw an exception, let the user continue to desk
	if cint(capkpi.db.get_single_value("System Settings", "setup_complete")):
		return {"status": "ok"}

	args = parse_args(args)

	stages = get_setup_stages(args)

	try:
		capkpi.flags.in_setup_wizard = True
		current_task = None
		for idx, stage in enumerate(stages):
			capkpi.publish_realtime(
				"setup_task",
				{"progress": [idx, len(stages)], "stage_status": stage.get("status")},
				user=capkpi.session.user,
			)

			for task in stage.get("tasks"):
				current_task = task
				task.get("fn")(task.get("args"))
	except Exception:
		handle_setup_exception(args)
		return {"status": "fail", "fail": current_task.get("fail_msg")}
	else:
		run_setup_success(args)
		return {"status": "ok"}
	finally:
		capkpi.flags.in_setup_wizard = False


def update_global_settings(args):
	if args.language and args.language != "English":
		set_default_language(get_language_code(args.lang))
		capkpi.db.commit()
	capkpi.clear_cache()

	update_system_settings(args)
	update_user_name(args)


def run_post_setup_complete(args):
	disable_future_access()
	capkpi.db.commit()
	capkpi.clear_cache()


def run_setup_success(args):
	for hook in capkpi.get_hooks("setup_wizard_success"):
		capkpi.get_attr(hook)(args)
	install_fixtures.install()


def get_stages_hooks(args):
	stages = []
	for method in capkpi.get_hooks("setup_wizard_stages"):
		stages += capkpi.get_attr(method)(args)
	return stages


def get_setup_complete_hooks(args):
	stages = []
	for method in capkpi.get_hooks("setup_wizard_complete"):
		stages.append(
			{
				"status": "Executing method",
				"fail_msg": "Failed to execute method",
				"tasks": [
					{"fn": capkpi.get_attr(method), "args": args, "fail_msg": "Failed to execute method"}
				],
			}
		)
	return stages


def handle_setup_exception(args):
	capkpi.db.rollback()
	if args:
		traceback = capkpi.get_traceback()
		print(traceback)
		for hook in capkpi.get_hooks("setup_wizard_exception"):
			capkpi.get_attr(hook)(traceback, args)


def update_system_settings(args):
	number_format = get_country_info(args.get("country")).get("number_format", "#,###.##")

	# replace these as float number formats, as they have 0 precision
	# and are currency number formats and not for floats
	if number_format == "#.###":
		number_format = "#.###,##"
	elif number_format == "#,###":
		number_format = "#,###.##"

	system_settings = capkpi.get_doc("System Settings", "System Settings")
	system_settings.update(
		{
			"country": args.get("country"),
			"language": get_language_code(args.get("language")) or "en",
			"time_zone": args.get("timezone"),
			"float_precision": 3,
			"date_format": capkpi.db.get_value("Country", args.get("country"), "date_format"),
			"time_format": capkpi.db.get_value("Country", args.get("country"), "time_format"),
			"number_format": number_format,
			"enable_scheduler": 1 if not capkpi.flags.in_test else 0,
			"backup_limit": 3,  # Default for downloadable backups
		}
	)
	system_settings.save()


def update_user_name(args):
	first_name, last_name = args.get("full_name", ""), ""
	if " " in first_name:
		first_name, last_name = first_name.split(" ", 1)

	if args.get("email"):
		if capkpi.db.exists("User", args.get("email")):
			# running again
			return

		args["name"] = args.get("email")

		_mute_emails, capkpi.flags.mute_emails = capkpi.flags.mute_emails, True
		doc = capkpi.get_doc(
			{
				"doctype": "User",
				"email": args.get("email"),
				"first_name": first_name,
				"last_name": last_name,
			}
		)
		doc.flags.no_welcome_mail = True
		doc.insert()
		capkpi.flags.mute_emails = _mute_emails
		update_password(args.get("email"), args.get("password"))

	elif first_name:
		args.update({"name": capkpi.session.user, "first_name": first_name, "last_name": last_name})

		capkpi.db.sql(
			"""update `tabUser` SET first_name=%(first_name)s,
			last_name=%(last_name)s WHERE name=%(name)s""",
			args,
		)

	if args.get("attach_user"):
		attach_user = args.get("attach_user").split(",")
		if len(attach_user) == 3:
			filename, filetype, content = attach_user
			_file = capkpi.get_doc(
				{
					"doctype": "File",
					"file_name": filename,
					"attached_to_doctype": "User",
					"attached_to_name": args.get("name"),
					"content": content,
					"decode": True,
				}
			)
			_file.save()
			fileurl = _file.file_url
			capkpi.db.set_value("User", args.get("name"), "user_image", fileurl)

	if args.get("name"):
		add_all_roles_to(args.get("name"))


def parse_args(args):
	if not args:
		args = capkpi.local.form_dict
	if isinstance(args, string_types):
		args = json.loads(args)

	args = capkpi._dict(args)

	# strip the whitespace
	for key, value in args.items():
		if isinstance(value, string_types):
			args[key] = strip(value)

	return args


def add_all_roles_to(name):
	user = capkpi.get_doc("User", name)
	for role in capkpi.db.sql("""select name from tabRole"""):
		if role[0] not in [
			"Administrator",
			"Guest",
			"All",
			"Customer",
			"Supplier",
			"Partner",
			"Employee",
		]:
			d = user.append("roles")
			d.role = role[0]
	user.save()


def disable_future_access():
	capkpi.db.set_default("desktop:home_page", "workspace")
	capkpi.db.set_value("System Settings", "System Settings", "setup_complete", 1)
	capkpi.db.set_value("System Settings", "System Settings", "is_first_startup", 1)

	# Enable onboarding after install
	capkpi.db.set_value("System Settings", "System Settings", "enable_onboarding", 1)

	if not capkpi.flags.in_test:
		# remove all roles and add 'Administrator' to prevent future access
		page = capkpi.get_doc("Page", "setup-wizard")
		page.roles = []
		page.append("roles", {"role": "Administrator"})
		page.flags.do_not_update_json = True
		page.flags.ignore_permissions = True
		page.save()


@capkpi.whitelist()
def load_messages(language):
	"""Load translation messages for given language from all `setup_wizard_requires`
	javascript files"""
	capkpi.clear_cache()
	set_default_language(get_language_code(language))
	capkpi.db.commit()
	m = get_dict("page", "setup-wizard")

	for path in capkpi.get_hooks("setup_wizard_requires"):
		# common folder `assets` served from `sites/`
		js_file_path = os.path.abspath(capkpi.get_site_path("..", *path.strip("/").split("/")))
		m.update(get_dict("jsfile", js_file_path))

	m.update(get_dict("boot"))
	send_translations(m)
	return capkpi.local.lang


@capkpi.whitelist()
def load_languages():
	language_codes = capkpi.db.sql(
		"select language_code, language_name from tabLanguage order by name", as_dict=True
	)
	codes_to_names = {}
	for d in language_codes:
		codes_to_names[d.language_code] = d.language_name
	return {
		"default_language": capkpi.db.get_value("Language", capkpi.local.lang, "language_name")
		or capkpi.local.lang,
		"languages": sorted(capkpi.db.sql_list("select language_name from tabLanguage order by name")),
		"codes_to_names": codes_to_names,
	}


@capkpi.whitelist()
def load_country():
	from capkpi.sessions import get_geo_ip_country

	return get_geo_ip_country(capkpi.local.request_ip) if capkpi.local.request_ip else None


@capkpi.whitelist()
def load_user_details():
	return {
		"full_name": capkpi.cache().hget("full_name", "signup"),
		"email": capkpi.cache().hget("email", "signup"),
	}


@capkpi.whitelist()
def reset_is_first_startup():
	capkpi.db.set_value("System Settings", "System Settings", "is_first_startup", 0)


def prettify_args(args):
	# remove attachments
	for key, val in args.items():
		if isinstance(val, string_types) and "data:image" in val:
			filename = val.split("data:image", 1)[0].strip(", ")
			size = round((len(val) * 3 / 4) / 1048576.0, 2)
			args[key] = "Image Attached: '{0}' of size {1} MB".format(filename, size)

	pretty_args = []
	for key in sorted(args):
		pretty_args.append("{} = {}".format(key, args[key]))
	return pretty_args


def email_setup_wizard_exception(traceback, args):
	if not capkpi.local.conf.setup_wizard_exception_email:
		return

	pretty_args = prettify_args(args)

	if capkpi.local.request:
		user_agent = UserAgent(capkpi.local.request.headers.get("User-Agent", ""))

	else:
		user_agent = capkpi._dict()

	message = """

#### Traceback

<pre>{traceback}</pre>

---

#### Setup Wizard Arguments

<pre>{args}</pre>

---

#### Request Headers

<pre>{headers}</pre>

---

#### Basic Information

- **Site:** {site}
- **User:** {user}
- **Browser:** {user_agent.platform} {user_agent.browser} version: {user_agent.version} language: {user_agent.language}
- **Browser Languages**: `{accept_languages}`""".format(
		site=capkpi.local.site,
		traceback=traceback,
		args="\n".join(pretty_args),
		user=capkpi.session.user,
		user_agent=user_agent,
		headers=capkpi.local.request.headers,
		accept_languages=", ".join(capkpi.local.request.accept_languages.values()),
	)

	capkpi.sendmail(
		recipients=capkpi.local.conf.setup_wizard_exception_email,
		sender=capkpi.session.user,
		subject="Setup failed: {}".format(capkpi.local.site),
		message=message,
		delayed=False,
	)


def log_setup_wizard_exception(traceback, args):
	with open("../logs/setup-wizard.log", "w+") as setup_log:
		setup_log.write(traceback)
		setup_log.write(json.dumps(args))


def get_language_code(lang):
	return capkpi.db.get_value("Language", {"language_name": lang})


def enable_twofactor_all_roles():
	all_role = capkpi.get_doc("Role", {"role_name": "All"})
	all_role.two_factor_auth = True
	all_role.save(ignore_permissions=True)


def make_records(records, debug=False):
	from capkpi import _dict
	from capkpi.modules import scrub

	if debug:
		print("make_records: in DEBUG mode")

	# LOG every success and failure
	for record in records:

		doctype = record.get("doctype")
		condition = record.get("__condition")

		if condition and not condition():
			continue

		doc = capkpi.new_doc(doctype)
		doc.update(record)

		# ignore mandatory for root
		parent_link_field = "parent_" + scrub(doc.doctype)
		if doc.meta.get_field(parent_link_field) and not doc.get(parent_link_field):
			doc.flags.ignore_mandatory = True

		try:
			doc.insert(ignore_permissions=True)

		except capkpi.DuplicateEntryError as e:
			# print("Failed to insert duplicate {0} {1}".format(doctype, doc.name))

			# pass DuplicateEntryError and continue
			if e.args and e.args[0] == doc.doctype and e.args[1] == doc.name:
				# make sure DuplicateEntryError is for the exact same doc and not a related doc
				capkpi.clear_messages()
			else:
				raise

		except Exception as e:
			exception = record.get("__exception")
			if exception:
				config = _dict(exception)
				if isinstance(e, config.exception):
					config.handler()
				else:
					show_document_insert_error()
			else:
				show_document_insert_error()


def show_document_insert_error():
	print("Document Insert Error")
	print(capkpi.get_traceback())
