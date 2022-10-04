# Copyright (c) 2021, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

"""
Boot session from cache or build

Session bootstraps info needed by common client side activities including
permission, homepage, default variables, system defaults etc
"""
import json

import redis
from six import text_type
from six.moves.urllib.parse import unquote

import capkpi
import capkpi.defaults
import capkpi.model.meta
import capkpi.translate
import capkpi.utils
from capkpi import _
from capkpi.cache_manager import clear_user_cache
from capkpi.utils import cint, cstr


@capkpi.whitelist()
def clear():
	capkpi.local.session_obj.update(force=True)
	capkpi.local.db.commit()
	clear_user_cache(capkpi.session.user)
	capkpi.response["message"] = _("Cache Cleared")


def clear_sessions(user=None, keep_current=False, device=None, force=False):
	"""Clear other sessions of the current user. Called at login / logout

	:param user: user name (default: current user)
	:param keep_current: keep current session (default: false)
	:param device: delete sessions of this device (default: desktop, mobile)
	:param force: triggered by the user (default false)
	"""

	reason = "Logged In From Another Session"
	if force:
		reason = "Force Logged out by the user"

	for sid in get_sessions_to_clear(user, keep_current, device):
		delete_session(sid, reason=reason)


def get_sessions_to_clear(user=None, keep_current=False, device=None):
	"""Returns sessions of the current user. Called at login / logout

	:param user: user name (default: current user)
	:param keep_current: keep current session (default: false)
	:param device: delete sessions of this device (default: desktop, mobile)
	"""
	if not user:
		user = capkpi.session.user

	if not device:
		device = ("desktop", "mobile")

	if not isinstance(device, (tuple, list)):
		device = (device,)

	offset = 0
	if user == capkpi.session.user:
		simultaneous_sessions = capkpi.db.get_value("User", user, "simultaneous_sessions") or 1
		offset = simultaneous_sessions - 1

	condition = ""
	if keep_current:
		condition = " AND sid != {0}".format(capkpi.db.escape(capkpi.session.sid))

	return capkpi.db.sql_list(
		"""
		SELECT `sid` FROM `tabSessions`
		WHERE `tabSessions`.user=%(user)s
		AND device in %(device)s
		{condition}
		ORDER BY `lastupdate` DESC
		LIMIT 100 OFFSET {offset}""".format(
			condition=condition, offset=offset
		),
		{"user": user, "device": device},
	)


def delete_session(sid=None, user=None, reason="Session Expired"):
	from capkpi.core.doctype.activity_log.feed import logout_feed

	capkpi.cache().hdel("session", sid)
	capkpi.cache().hdel("last_db_session_update", sid)
	if sid and not user:
		user_details = capkpi.db.sql("""select user from tabSessions where sid=%s""", sid, as_dict=True)
		if user_details:
			user = user_details[0].get("user")

	logout_feed(user, reason)
	capkpi.db.sql("""delete from tabSessions where sid=%s""", sid)
	capkpi.db.commit()


def clear_all_sessions(reason=None):
	"""This effectively logs out all users"""
	capkpi.only_for("Administrator")
	if not reason:
		reason = "Deleted All Active Session"
	for sid in capkpi.db.sql_list("select sid from `tabSessions`"):
		delete_session(sid, reason=reason)


def get_expired_sessions():
	"""Returns list of expired sessions"""
	expired = []
	for device in ("desktop", "mobile"):
		expired += capkpi.db.sql_list(
			"""SELECT `sid`
				FROM `tabSessions`
				WHERE (NOW() - `lastupdate`) > %s
				AND device = %s""",
			(get_expiry_period_for_query(device), device),
		)

	return expired


def clear_expired_sessions():
	"""This function is meant to be called from scheduler"""
	for sid in get_expired_sessions():
		delete_session(sid, reason="Session Expired")


def get():
	"""get session boot info"""
	from capkpi.boot import get_bootinfo, get_unseen_notes
	from capkpi.utils.change_log import get_change_log

	bootinfo = None
	if not getattr(capkpi.conf, "disable_session_cache", None):
		# check if cache exists
		bootinfo = capkpi.cache().hget("bootinfo", capkpi.session.user)
		if bootinfo:
			bootinfo["from_cache"] = 1
			bootinfo["user"]["recent"] = json.dumps(capkpi.cache().hget("user_recent", capkpi.session.user))

	if not bootinfo:
		# if not create it
		bootinfo = get_bootinfo()
		capkpi.cache().hset("bootinfo", capkpi.session.user, bootinfo)
		try:
			capkpi.cache().ping()
		except redis.exceptions.ConnectionError:
			message = _("Redis cache server not running. Please contact Administrator / Tech support")
			if "messages" in bootinfo:
				bootinfo["messages"].append(message)
			else:
				bootinfo["messages"] = [message]

		# check only when clear cache is done, and don't cache this
		if capkpi.local.request:
			bootinfo["change_log"] = get_change_log()

	bootinfo["metadata_version"] = capkpi.cache().get_value("metadata_version")
	if not bootinfo["metadata_version"]:
		bootinfo["metadata_version"] = capkpi.reset_metadata_version()

	bootinfo.notes = get_unseen_notes()

	for hook in capkpi.get_hooks("extend_bootinfo"):
		capkpi.get_attr(hook)(bootinfo=bootinfo)

	bootinfo["lang"] = capkpi.translate.get_user_lang()
	bootinfo["disable_async"] = capkpi.conf.disable_async

	bootinfo["setup_complete"] = cint(capkpi.db.get_single_value("System Settings", "setup_complete"))
	bootinfo["is_first_startup"] = cint(
		capkpi.db.get_single_value("System Settings", "is_first_startup")
	)

	return bootinfo


def get_csrf_token():
	if not capkpi.local.session.data.csrf_token:
		generate_csrf_token()

	return capkpi.local.session.data.csrf_token


def generate_csrf_token():
	capkpi.local.session.data.csrf_token = capkpi.generate_hash()
	capkpi.local.session_obj.update(force=True)


class Session:
	def __init__(self, user, resume=False, full_name=None, user_type=None):
		self.sid = cstr(
			capkpi.form_dict.get("sid") or unquote(capkpi.request.cookies.get("sid", "Guest"))
		)
		self.user = user
		self.device = capkpi.form_dict.get("device") or "desktop"
		self.user_type = user_type
		self.full_name = full_name
		self.data = capkpi._dict({"data": capkpi._dict({})})
		self.time_diff = None

		# set local session
		capkpi.local.session = self.data

		if resume:
			self.resume()

		else:
			if self.user:
				self.start()

	def start(self):
		"""start a new session"""
		# generate sid
		if self.user == "Guest":
			sid = "Guest"
		else:
			sid = capkpi.generate_hash()

		self.data.user = self.user
		self.data.sid = sid
		self.data.data.user = self.user
		self.data.data.session_ip = capkpi.local.request_ip
		if self.user != "Guest":
			self.data.data.update(
				{
					"last_updated": capkpi.utils.now(),
					"session_expiry": get_expiry_period(self.device),
					"full_name": self.full_name,
					"user_type": self.user_type,
					"device": self.device,
					"session_country": get_geo_ip_country(capkpi.local.request_ip)
					if capkpi.local.request_ip
					else None,
				}
			)

		# insert session
		if self.user != "Guest":
			self.insert_session_record()

			# update user
			user = capkpi.get_doc("User", self.data["user"])
			capkpi.db.sql(
				"""UPDATE `tabUser`
				SET
					last_login = %(now)s,
					last_ip = %(ip)s,
					last_active = %(now)s
				WHERE name=%(name)s""",
				{"now": capkpi.utils.now(), "ip": capkpi.local.request_ip, "name": self.data["user"]},
			)
			user.run_notifications("before_change")
			user.run_notifications("on_update")
			capkpi.db.commit()

	def insert_session_record(self):
		capkpi.db.sql(
			"""insert into `tabSessions`
			(`sessiondata`, `user`, `lastupdate`, `sid`, `status`, `device`)
			values (%s , %s, NOW(), %s, 'Active', %s)""",
			(str(self.data["data"]), self.data["user"], self.data["sid"], self.device),
		)

		# also add to memcache
		capkpi.cache().hset("session", self.data.sid, self.data)

	def resume(self):
		"""non-login request: load a session"""
		import capkpi
		from capkpi.auth import validate_ip_address

		data = self.get_session_record()

		if data:
			self.data.update({"data": data, "user": data.user, "sid": self.sid})
			self.user = data.user
			validate_ip_address(self.user)
			self.device = data.device
		else:
			self.start_as_guest()

		if self.sid != "Guest":
			capkpi.local.user_lang = capkpi.translate.get_user_lang(self.data.user)
			capkpi.local.lang = capkpi.local.user_lang

	def get_session_record(self):
		"""get session record, or return the standard Guest Record"""
		from capkpi.auth import clear_cookies

		r = self.get_session_data()

		if not r:
			capkpi.response["session_expired"] = 1
			clear_cookies()
			self.sid = "Guest"
			r = self.get_session_data()

		return r

	def get_session_data(self):
		if self.sid == "Guest":
			return capkpi._dict({"user": "Guest"})

		data = self.get_session_data_from_cache()
		if not data:
			data = self.get_session_data_from_db()
		return data

	def get_session_data_from_cache(self):
		data = capkpi.cache().hget("session", self.sid)
		if data:
			data = capkpi._dict(data)
			session_data = data.get("data", {})

			# set user for correct timezone
			self.time_diff = capkpi.utils.time_diff_in_seconds(
				capkpi.utils.now(), session_data.get("last_updated")
			)
			expiry = get_expiry_in_seconds(session_data.get("session_expiry"))

			if self.time_diff > expiry:
				self._delete_session()
				data = None

		return data and data.data

	def get_session_data_from_db(self):
		self.device = capkpi.db.sql("SELECT `device` FROM `tabSessions` WHERE `sid`=%s", self.sid)
		self.device = self.device and self.device[0][0] or "desktop"

		rec = capkpi.db.sql(
			"""
			SELECT `user`, `sessiondata`
			FROM `tabSessions` WHERE `sid`=%s AND
			(NOW() - lastupdate) < %s
			""",
			(self.sid, get_expiry_period_for_query(self.device)),
		)

		if rec:
			data = capkpi._dict(eval(rec and rec[0][1] or "{}"))
			data.user = rec[0][0]
		else:
			self._delete_session()
			data = None

		return data

	def _delete_session(self):
		delete_session(self.sid, reason="Session Expired")

	def start_as_guest(self):
		"""all guests share the same 'Guest' session"""
		self.user = "Guest"
		self.start()

	def update(self, force=False):
		"""extend session expiry"""
		if capkpi.session["user"] == "Guest" or capkpi.form_dict.cmd == "logout":
			return

		now = capkpi.utils.now()

		self.data["data"]["last_updated"] = now
		self.data["data"]["lang"] = str(capkpi.lang)

		# update session in db
		last_updated = capkpi.cache().hget("last_db_session_update", self.sid)
		time_diff = capkpi.utils.time_diff_in_seconds(now, last_updated) if last_updated else None

		# database persistence is secondary, don't update it too often
		updated_in_db = False
		if force or (time_diff == None) or (time_diff > 600):
			# update sessions table
			capkpi.db.sql(
				"""update `tabSessions` set sessiondata=%s,
				lastupdate=NOW() where sid=%s""",
				(str(self.data["data"]), self.data["sid"]),
			)

			# update last active in user table
			capkpi.db.sql(
				"""update `tabUser` set last_active=%(now)s where name=%(name)s""",
				{"now": now, "name": capkpi.session.user},
			)

			capkpi.db.commit()
			capkpi.cache().hset("last_db_session_update", self.sid, now)

			updated_in_db = True

		# set in memcache
		capkpi.cache().hset("session", self.sid, self.data)

		return updated_in_db


def get_expiry_period_for_query(device=None):
	if capkpi.db.db_type == "postgres":
		return get_expiry_period(device)
	else:
		return get_expiry_in_seconds(device=device)


def get_expiry_in_seconds(expiry=None, device=None):
	if not expiry:
		expiry = get_expiry_period(device)
	parts = expiry.split(":")
	return (cint(parts[0]) * 3600) + (cint(parts[1]) * 60) + cint(parts[2])


def get_expiry_period(device="desktop"):
	if device == "mobile":
		key = "session_expiry_mobile"
		default = "720:00:00"
	else:
		key = "session_expiry"
		default = "06:00:00"

	exp_sec = capkpi.defaults.get_global_default(key) or default

	# incase seconds is missing
	if len(exp_sec.split(":")) == 2:
		exp_sec = exp_sec + ":00"

	return exp_sec


def get_geo_from_ip(ip_addr):
	try:
		from geolite2 import geolite2

		with geolite2 as f:
			reader = f.reader()
			data = reader.get(ip_addr)

			return capkpi._dict(data)
	except ImportError:
		return
	except ValueError:
		return
	except TypeError:
		return


def get_geo_ip_country(ip_addr):
	match = get_geo_from_ip(ip_addr)
	if match:
		return match.country
