# -*- coding: utf-8 -*-
# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import logging
import os

from six import iteritems
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.local import LocalManager
from werkzeug.middleware.profiler import ProfilerMiddleware
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wrappers import Request, Response

import capkpi
import capkpi.api
import capkpi.auth
import capkpi.handler
import capkpi.monitor
import capkpi.rate_limiter
import capkpi.recorder
import capkpi.utils.response
import capkpi.website.render
from capkpi import _
from capkpi.core.doctype.comment.comment import update_comments_in_parent_after_request
from capkpi.middlewares import StaticDataMiddleware
from capkpi.utils import get_site_name, sanitize_html
from capkpi.utils.error import make_error_snapshot

local_manager = LocalManager([capkpi.local])

_site = None
_sites_path = os.environ.get("SITES_PATH", ".")


class RequestContext(object):
	def __init__(self, environ):
		self.request = Request(environ)

	def __enter__(self):
		init_request(self.request)

	def __exit__(self, type, value, traceback):
		capkpi.destroy()


@Request.application
def application(request):
	response = None

	try:
		rollback = True

		init_request(request)

		capkpi.recorder.record()
		capkpi.monitor.start()
		capkpi.rate_limiter.apply()
		capkpi.api.validate_auth()

		if request.method == "OPTIONS":
			response = Response()

		elif capkpi.form_dict.cmd:
			response = capkpi.handler.handle()

		elif request.path.startswith("/api/"):
			response = capkpi.api.handle()

		elif request.path.startswith("/backups"):
			response = capkpi.utils.response.download_backup(request.path)

		elif request.path.startswith("/private/files/"):
			response = capkpi.utils.response.download_private_file(request.path)

		elif request.method in ("GET", "HEAD", "POST"):
			response = capkpi.website.render.render()

		else:
			raise NotFound

	except HTTPException as e:
		return e

	except capkpi.SessionStopped as e:
		response = capkpi.utils.response.handle_session_stopped()

	except Exception as e:
		response = handle_exception(e)

	else:
		rollback = after_request(rollback)

	finally:
		if request.method in ("POST", "PUT") and capkpi.db and rollback:
			capkpi.db.rollback()

		capkpi.rate_limiter.update()
		capkpi.monitor.stop(response)
		capkpi.recorder.dump()

		log_request(request, response)
		process_response(response)
		capkpi.destroy()

	return response


def init_request(request):
	capkpi.local.request = request
	capkpi.local.is_ajax = capkpi.get_request_header("X-Requested-With") == "XMLHttpRequest"

	site = _site or request.headers.get("X-CapKPI-Site-Name") or get_site_name(request.host)
	capkpi.init(site=site, sites_path=_sites_path)

	if not (capkpi.local.conf and capkpi.local.conf.db_name):
		# site does not exist
		raise NotFound

	if capkpi.local.conf.get("maintenance_mode"):
		capkpi.connect()
		raise capkpi.SessionStopped("Session Stopped")
	else:
		capkpi.connect(set_admin_as_user=False)

	make_form_dict(request)

	if request.method != "OPTIONS":
		capkpi.local.http_request = capkpi.auth.HTTPRequest()


def log_request(request, response):
	if hasattr(capkpi.local, "conf") and capkpi.local.conf.enable_capkpi_logger:
		capkpi.logger("capkpi.web", allow_site=capkpi.local.site).info(
			{
				"site": get_site_name(request.host),
				"remote_addr": getattr(request, "remote_addr", "NOTFOUND"),
				"base_url": getattr(request, "base_url", "NOTFOUND"),
				"full_path": getattr(request, "full_path", "NOTFOUND"),
				"method": getattr(request, "method", "NOTFOUND"),
				"scheme": getattr(request, "scheme", "NOTFOUND"),
				"http_status_code": getattr(response, "status_code", "NOTFOUND"),
			}
		)


def process_response(response):
	if not response:
		return

	# set cookies
	if hasattr(capkpi.local, "cookie_manager"):
		capkpi.local.cookie_manager.flush_cookies(response=response)

	# rate limiter headers
	if hasattr(capkpi.local, "rate_limiter"):
		response.headers.extend(capkpi.local.rate_limiter.headers())

	# CORS headers
	if hasattr(capkpi.local, "conf") and capkpi.conf.allow_cors:
		set_cors_headers(response)


def set_cors_headers(response):
	origin = capkpi.request.headers.get("Origin")
	allow_cors = capkpi.conf.allow_cors
	if not (origin and allow_cors):
		return

	if allow_cors != "*":
		if not isinstance(allow_cors, list):
			allow_cors = [allow_cors]

		if origin not in allow_cors:
			return

	response.headers.extend(
		{
			"Access-Control-Allow-Origin": origin,
			"Access-Control-Allow-Credentials": "true",
			"Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
			"Access-Control-Allow-Headers": (
				"Authorization,DNT,X-Mx-ReqToken,"
				"Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,"
				"Cache-Control,Content-Type"
			),
		}
	)


def make_form_dict(request):
	import json

	request_data = request.get_data(as_text=True)
	if "application/json" in (request.content_type or "") and request_data:
		args = json.loads(request_data)
	else:
		args = {}
		args.update(request.args or {})
		args.update(request.form or {})

	if not isinstance(args, dict):
		capkpi.throw("Invalid request arguments")

	try:
		capkpi.local.form_dict = capkpi._dict(
			{k: v[0] if isinstance(v, (list, tuple)) else v for k, v in iteritems(args)}
		)
	except IndexError:
		capkpi.local.form_dict = capkpi._dict(args)

	if "_" in capkpi.local.form_dict:
		# _ is passed by $.ajax so that the request is not cached by the browser. So, remove _ from form_dict
		capkpi.local.form_dict.pop("_")


def handle_exception(e):
	response = None
	http_status_code = getattr(e, "http_status_code", 500)
	return_as_message = False
	accept_header = capkpi.get_request_header("Accept") or ""
	respond_as_json = (
		capkpi.get_request_header("Accept")
		and (capkpi.local.is_ajax or "application/json" in accept_header)
		or (capkpi.local.request.path.startswith("/api/") and not accept_header.startswith("text"))
	)

	if respond_as_json:
		# handle ajax responses first
		# if the request is ajax, send back the trace or error message
		response = capkpi.utils.response.report_error(http_status_code)

	elif (
		http_status_code == 500
		and (capkpi.db and isinstance(e, capkpi.db.InternalError))
		and (capkpi.db and (capkpi.db.is_deadlocked(e) or capkpi.db.is_timedout(e)))
	):
		http_status_code = 508

	elif http_status_code == 401:
		capkpi.respond_as_web_page(
			_("Session Expired"),
			_("Your session has expired, please login again to continue."),
			http_status_code=http_status_code,
			indicator_color="red",
		)
		return_as_message = True

	elif http_status_code == 403:
		capkpi.respond_as_web_page(
			_("Not Permitted"),
			_("You do not have enough permissions to complete the action"),
			http_status_code=http_status_code,
			indicator_color="red",
		)
		return_as_message = True

	elif http_status_code == 404:
		capkpi.respond_as_web_page(
			_("Not Found"),
			_("The resource you are looking for is not available"),
			http_status_code=http_status_code,
			indicator_color="red",
		)
		return_as_message = True

	elif http_status_code == 429:
		response = capkpi.rate_limiter.respond()

	else:
		traceback = "<pre>" + sanitize_html(capkpi.get_traceback()) + "</pre>"
		# disable traceback in production if flag is set
		if capkpi.local.flags.disable_traceback and not capkpi.local.dev_server:
			traceback = ""

		capkpi.respond_as_web_page(
			"Server Error", traceback, http_status_code=http_status_code, indicator_color="red", width=640
		)
		return_as_message = True

	if e.__class__ == capkpi.AuthenticationError:
		if hasattr(capkpi.local, "login_manager"):
			capkpi.local.login_manager.clear_cookies()

	if http_status_code >= 500:
		make_error_snapshot(e)

	if return_as_message:
		response = capkpi.website.render.render("message", http_status_code=http_status_code)

	if capkpi.conf.get("developer_mode") and not respond_as_json:
		# don't fail silently for non-json response errors
		print(capkpi.get_traceback())

	return response


def after_request(rollback):
	if (capkpi.local.request.method in ("POST", "PUT") or capkpi.local.flags.commit) and capkpi.db:
		if capkpi.db.transaction_writes:
			capkpi.db.commit()
			rollback = False

	# update session
	if getattr(capkpi.local, "session_obj", None):
		updated_in_db = capkpi.local.session_obj.update()
		if updated_in_db:
			capkpi.db.commit()
			rollback = False

	update_comments_in_parent_after_request()

	return rollback


application = local_manager.make_middleware(application)


def serve(
	port=8000, profile=False, no_reload=False, no_threading=False, site=None, sites_path="."
):
	global application, _site, _sites_path
	_site = site
	_sites_path = sites_path

	from werkzeug.serving import run_simple

	patch_werkzeug_reloader()

	if profile:
		application = ProfilerMiddleware(application, sort_by=("cumtime", "calls"))

	if not os.environ.get("NO_STATICS"):
		application = SharedDataMiddleware(
			application, {str("/assets"): str(os.path.join(sites_path, "assets"))}
		)

		application = StaticDataMiddleware(
			application, {str("/files"): str(os.path.abspath(sites_path))}
		)

	application.debug = True
	application.config = {"SERVER_NAME": "localhost:8000"}

	log = logging.getLogger("werkzeug")
	log.propagate = False

	in_test_env = os.environ.get("CI")
	if in_test_env:
		log.setLevel(logging.ERROR)

	run_simple(
		"0.0.0.0",
		int(port),
		application,
		use_reloader=False if in_test_env else not no_reload,
		use_debugger=not in_test_env,
		use_evalex=not in_test_env,
		threaded=not no_threading,
	)


def patch_werkzeug_reloader():
	"""
	This function monkey patches Werkzeug reloader to ignore reloading files in
	the __pycache__ directory.

	To be deprecated when upgrading to Werkzeug 2.
	"""

	from werkzeug._reloader import WatchdogReloaderLoop

	trigger_reload = WatchdogReloaderLoop.trigger_reload

	def custom_trigger_reload(self, filename):
		if os.path.basename(os.path.dirname(filename)) == "__pycache__":
			return

		return trigger_reload(self, filename)

	WatchdogReloaderLoop.trigger_reload = custom_trigger_reload
