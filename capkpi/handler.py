# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

from werkzeug.wrappers import Response

import capkpi
import capkpi.sessions
import capkpi.utils
from capkpi import _, is_whitelisted
from capkpi.core.doctype.server_script.server_script_utils import get_server_script_map
from capkpi.utils import cint
from capkpi.utils.csvutils import build_csv_response
from capkpi.utils.response import build_response

ALLOWED_MIMETYPES = (
	"image/png",
	"image/jpeg",
	"application/pdf",
	"application/msword",
	"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
	"application/vnd.ms-excel",
	"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
	"application/vnd.oasis.opendocument.text",
	"application/vnd.oasis.opendocument.spreadsheet",
	"text/plain",
)


def handle():
	"""handle request"""

	cmd = capkpi.local.form_dict.cmd
	data = None

	if cmd != "login":
		data = execute_cmd(cmd)

	# data can be an empty string or list which are valid responses
	if data is not None:
		if isinstance(data, Response):
			# method returns a response object, pass it on
			return data

		# add the response to `message` label
		capkpi.response["message"] = data

	return build_response("json")


def execute_cmd(cmd, from_async=False):
	"""execute a request as python module"""
	for hook in capkpi.get_hooks("override_whitelisted_methods", {}).get(cmd, []):
		# override using the first hook
		cmd = hook
		break

	# via server script
	server_script = get_server_script_map().get("_api", {}).get(cmd)
	if server_script:
		return run_server_script(server_script)

	try:
		method = get_attr(cmd)
	except Exception as e:
		capkpi.throw(_("Failed to get method for command {0} with {1}").format(cmd, e))

	if from_async:
		method = method.queue

	if method != run_doc_method:
		is_whitelisted(method)
		is_valid_http_method(method)

	return capkpi.call(method, **capkpi.form_dict)


def run_server_script(server_script):
	response = capkpi.get_doc("Server Script", server_script).execute_method()

	# some server scripts return output using flags (empty dict by default),
	# while others directly modify capkpi.response
	# return flags if not empty dict (this overwrites capkpi.response.message)
	if response != {}:
		return response


def is_valid_http_method(method):
	if capkpi.flags.in_safe_exec:
		return

	http_method = capkpi.local.request.method

	if http_method not in capkpi.allowed_http_methods_for_whitelisted_func[method]:
		throw_permission_error()


def throw_permission_error():
	capkpi.throw(_("Not permitted"), capkpi.PermissionError)


@capkpi.whitelist(allow_guest=True)
def version():
	return capkpi.__version__


@capkpi.whitelist(allow_guest=True)
def logout():
	capkpi.local.login_manager.logout()
	capkpi.db.commit()


@capkpi.whitelist(allow_guest=True)
def web_logout():
	capkpi.local.login_manager.logout()
	capkpi.db.commit()
	capkpi.respond_as_web_page(
		_("Logged Out"), _("You have been successfully logged out"), indicator_color="green"
	)


@capkpi.whitelist()
def uploadfile():
	ret = None

	try:
		if capkpi.form_dict.get("from_form"):
			try:
				ret = capkpi.get_doc(
					{
						"doctype": "File",
						"attached_to_name": capkpi.form_dict.docname,
						"attached_to_doctype": capkpi.form_dict.doctype,
						"attached_to_field": capkpi.form_dict.docfield,
						"file_url": capkpi.form_dict.file_url,
						"file_name": capkpi.form_dict.filename,
						"is_private": capkpi.utils.cint(capkpi.form_dict.is_private),
						"content": capkpi.form_dict.filedata,
						"decode": True,
					}
				)
				ret.save()
			except capkpi.DuplicateEntryError:
				# ignore pass
				ret = None
				capkpi.db.rollback()
		else:
			if capkpi.form_dict.get("method"):
				method = capkpi.get_attr(capkpi.form_dict.method)
				is_whitelisted(method)
				ret = method()
	except Exception:
		capkpi.errprint(capkpi.utils.get_traceback())
		capkpi.response["http_status_code"] = 500
		ret = None

	return ret


@capkpi.whitelist(allow_guest=True)
def upload_file():
	user = None
	if capkpi.session.user == "Guest":
		if capkpi.get_system_settings("allow_guests_to_upload_files"):
			ignore_permissions = True
		else:
			return
	else:
		user = capkpi.get_doc("User", capkpi.session.user)
		ignore_permissions = False

	files = capkpi.request.files
	is_private = capkpi.form_dict.is_private
	doctype = capkpi.form_dict.doctype
	docname = capkpi.form_dict.docname
	fieldname = capkpi.form_dict.fieldname
	file_url = capkpi.form_dict.file_url
	folder = capkpi.form_dict.folder or "Home"
	method = capkpi.form_dict.method
	filename = capkpi.form_dict.file_name
	content = None

	if "file" in files:
		file = files["file"]
		content = file.stream.read()
		filename = file.filename

	capkpi.local.uploaded_file = content
	capkpi.local.uploaded_filename = filename

	if content is not None and (
		capkpi.session.user == "Guest" or (user and not user.has_desk_access())
	):
		import mimetypes

		filetype = mimetypes.guess_type(filename)[0]
		if filetype not in ALLOWED_MIMETYPES:
			capkpi.throw(_("You can only upload JPG, PNG, PDF, TXT or Microsoft documents."))

	if method:
		method = capkpi.get_attr(method)
		is_whitelisted(method)
		return method()
	else:
		ret = capkpi.get_doc(
			{
				"doctype": "File",
				"attached_to_doctype": doctype,
				"attached_to_name": docname,
				"attached_to_field": fieldname,
				"folder": folder,
				"file_name": filename,
				"file_url": file_url,
				"is_private": cint(is_private),
				"content": content,
			}
		)
		ret.save(ignore_permissions=ignore_permissions)
		return ret


def get_attr(cmd):
	"""get method object from cmd"""
	if "." in cmd:
		method = capkpi.get_attr(cmd)
	else:
		method = globals()[cmd]
	capkpi.log("method:" + cmd)
	return method


@capkpi.whitelist(allow_guest=True)
def ping():
	return "pong"


def run_doc_method(method, docs=None, dt=None, dn=None, arg=None, args=None):
	"""run a whitelisted controller method"""
	import inspect
	import json

	if not args:
		args = arg or ""

	if dt:  # not called from a doctype (from a page)
		if not dn:
			dn = dt  # single
		doc = capkpi.get_doc(dt, dn)

	else:
		if isinstance(docs, str):
			docs = json.loads(docs)

		doc = capkpi.get_doc(docs)
		doc._original_modified = doc.modified
		doc.check_if_latest()

	if not doc or not doc.has_permission("read"):
		throw_permission_error()

	try:
		args = json.loads(args)
	except ValueError:
		args = args

	method_obj = getattr(doc, method)
	fn = getattr(method_obj, "__func__", method_obj)
	is_whitelisted(fn)
	is_valid_http_method(fn)

	fnargs = inspect.getfullargspec(method_obj).args

	if not fnargs or (len(fnargs) == 1 and fnargs[0] == "self"):
		response = doc.run_method(method)

	elif "args" in fnargs or not isinstance(args, dict):
		response = doc.run_method(method, args)

	else:
		response = doc.run_method(method, **args)

	capkpi.response.docs.append(doc)
	if not response:
		return

	# build output as csv
	if cint(capkpi.form_dict.get("as_csv")):
		build_csv_response(response, _(doc.doctype).replace(" ", ""))
		return

	capkpi.response["message"] = response


# for backwards compatibility
runserverobj = run_doc_method
