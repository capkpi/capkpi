# Copyright (c) 2021, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See LICENSE
from urllib.parse import quote

import capkpi
import capkpi.database
import capkpi.utils
import capkpi.utils.user
from capkpi import _, conf
from capkpi.core.doctype.activity_log.activity_log import add_authentication_log
from capkpi.modules.patch_handler import check_session_stopped
from capkpi.sessions import Session, clear_sessions, delete_session
from capkpi.translate import get_language
from capkpi.twofactor import (
	authenticate_for_2factor,
	confirm_otp_token,
	get_cached_user_pass,
	should_run_2fa,
)
from capkpi.utils import cint, date_diff, datetime, get_datetime, today
from capkpi.utils.password import check_password
from capkpi.website.utils import get_home_page


class HTTPRequest:
	def __init__(self):
		# set capkpi.local.request_ip
		self.set_request_ip()

		# load cookies
		self.set_cookies()

		# set capkpi.local.db
		self.connect()

		# login and start/resume user session
		self.set_session()

		# set request language
		self.set_lang()

		# match csrf token from current session
		self.validate_csrf_token()

		# write out latest cookies
		capkpi.local.cookie_manager.init_cookies()

		# check session status
		check_session_stopped()

	@property
	def domain(self):
		if not getattr(self, "_domain", None):
			self._domain = capkpi.request.host
			if self._domain and self._domain.startswith("www."):
				self._domain = self._domain[4:]

		return self._domain

	def set_request_ip(self):
		if capkpi.get_request_header("X-Forwarded-For"):
			capkpi.local.request_ip = (capkpi.get_request_header("X-Forwarded-For").split(",")[0]).strip()

		elif capkpi.get_request_header("REMOTE_ADDR"):
			capkpi.local.request_ip = capkpi.get_request_header("REMOTE_ADDR")

		else:
			capkpi.local.request_ip = "127.0.0.1"

	def set_cookies(self):
		capkpi.local.cookie_manager = CookieManager()

	def set_session(self):
		capkpi.local.login_manager = LoginManager()

	def validate_csrf_token(self):
		if capkpi.local.request and capkpi.local.request.method in ("POST", "PUT", "DELETE"):
			if not capkpi.local.session:
				return
			if (
				not capkpi.local.session.data.csrf_token
				or capkpi.local.session.data.device == "mobile"
				or capkpi.conf.get("ignore_csrf", None)
			):
				# not via boot
				return

			csrf_token = capkpi.get_request_header("X-CapKPI-CSRF-Token")
			if not csrf_token and "csrf_token" in capkpi.local.form_dict:
				csrf_token = capkpi.local.form_dict.csrf_token
				del capkpi.local.form_dict["csrf_token"]

			if capkpi.local.session.data.csrf_token != csrf_token:
				capkpi.local.flags.disable_traceback = True
				capkpi.throw(_("Invalid Request"), capkpi.CSRFTokenError)

	def set_lang(self):
		capkpi.local.lang = get_language()

	def get_db_name(self):
		"""get database name from conf"""
		return conf.db_name

	def connect(self):
		"""connect to db, from ac_name or db_name"""
		capkpi.local.db = capkpi.database.get_db(
			user=self.get_db_name(), password=getattr(conf, "db_password", "")
		)


class LoginManager:
	def __init__(self):
		self.user = None
		self.info = None
		self.full_name = None
		self.user_type = None

		if (
			capkpi.local.form_dict.get("cmd") == "login" or capkpi.local.request.path == "/api/method/login"
		):
			if self.login() == False:
				return
			self.resume = False

			# run login triggers
			self.run_trigger("on_session_creation")
		else:
			try:
				self.resume = True
				self.make_session(resume=True)
				self.get_user_info()
				self.set_user_info(resume=True)
			except AttributeError:
				self.user = "Guest"
				self.get_user_info()
				self.make_session()
				self.set_user_info()

	@capkpi.whitelist()
	def login(self):
		# clear cache
		capkpi.clear_cache(user=capkpi.form_dict.get("usr"))
		user, pwd = get_cached_user_pass()
		self.authenticate(user=user, pwd=pwd)
		if self.force_user_to_reset_password():
			doc = capkpi.get_doc("User", self.user)
			capkpi.local.response["redirect_to"] = doc.reset_password(
				send_email=False, password_expired=True
			)
			capkpi.local.response["message"] = "Password Reset"
			return False

		if should_run_2fa(self.user):
			authenticate_for_2factor(self.user)
			if not confirm_otp_token(self):
				return False
		capkpi.form_dict.pop("pwd", None)
		self.post_login()

	def post_login(self):
		self.run_trigger("on_login")
		validate_ip_address(self.user)
		self.validate_hour()
		self.get_user_info()
		self.make_session()
		self.setup_boot_cache()
		self.set_user_info()

	def get_user_info(self):
		self.info = capkpi.db.get_value(
			"User", self.user, ["user_type", "first_name", "last_name", "user_image"], as_dict=1
		)

		self.user_type = self.info.user_type

	def setup_boot_cache(self):
		capkpi.cache_manager.build_table_count_cache()
		capkpi.cache_manager.build_domain_restriced_doctype_cache()
		capkpi.cache_manager.build_domain_restriced_page_cache()

	def set_user_info(self, resume=False):
		# set sid again
		capkpi.local.cookie_manager.init_cookies()

		self.full_name = " ".join(filter(None, [self.info.first_name, self.info.last_name]))

		if self.info.user_type == "Website User":
			capkpi.local.cookie_manager.set_cookie("system_user", "no")
			if not resume:
				capkpi.local.response["message"] = "No App"
				capkpi.local.response["home_page"] = "/" + get_home_page()
		else:
			capkpi.local.cookie_manager.set_cookie("system_user", "yes")
			if not resume:
				capkpi.local.response["message"] = "Logged In"
				capkpi.local.response["home_page"] = "/app"

		if not resume:
			capkpi.response["full_name"] = self.full_name

		# redirect information
		redirect_to = capkpi.cache().hget("redirect_after_login", self.user)
		if redirect_to:
			capkpi.local.response["redirect_to"] = redirect_to
			capkpi.cache().hdel("redirect_after_login", self.user)

		capkpi.local.cookie_manager.set_cookie("full_name", self.full_name)
		capkpi.local.cookie_manager.set_cookie("user_id", self.user)
		capkpi.local.cookie_manager.set_cookie("user_image", self.info.user_image or "")

	def clear_preferred_language(self):
		capkpi.local.cookie_manager.delete_cookie("preferred_language")

	def make_session(self, resume=False):
		# start session
		capkpi.local.session_obj = Session(
			user=self.user, resume=resume, full_name=self.full_name, user_type=self.user_type
		)

		# reset user if changed to Guest
		self.user = capkpi.local.session_obj.user
		capkpi.local.session = capkpi.local.session_obj.data
		self.clear_active_sessions()

	def clear_active_sessions(self):
		"""Clear other sessions of the current user if `deny_multiple_sessions` is not set"""
		if not (
			cint(capkpi.conf.get("deny_multiple_sessions"))
			or cint(capkpi.db.get_system_setting("deny_multiple_sessions"))
		):
			return

		if capkpi.session.user != "Guest":
			clear_sessions(capkpi.session.user, keep_current=True)

	def authenticate(self, user: str = None, pwd: str = None):
		from capkpi.core.doctype.user.user import User

		if not (user and pwd):
			user, pwd = capkpi.form_dict.get("usr"), capkpi.form_dict.get("pwd")
		if not (user and pwd):
			self.fail(_("Incomplete login details"), user=user)

		user = User.find_by_credentials(user, pwd)

		if not user:
			self.fail("Invalid login credentials")

		# Current login flow uses cached credentials for authentication while checking OTP.
		# Incase of OTP check, tracker for auth needs to be disabled(If not, it can remove tracker history as it is going to succeed anyway)
		# Tracker is activated for 2FA incase of OTP.
		ignore_tracker = should_run_2fa(user.name) and ("otp" in capkpi.form_dict)
		tracker = None if ignore_tracker else get_login_attempt_tracker(user.name)

		if not user.is_authenticated:
			tracker and tracker.add_failure_attempt()
			self.fail("Invalid login credentials", user=user.name)
		elif not (user.name == "Administrator" or user.enabled):
			tracker and tracker.add_failure_attempt()
			self.fail("User disabled or missing", user=user.name)
		else:
			tracker and tracker.add_success_attempt()
		self.user = user.name

	def force_user_to_reset_password(self):
		if not self.user:
			return

		from capkpi.core.doctype.user.user import STANDARD_USERS

		if self.user in STANDARD_USERS:
			return False

		reset_pwd_after_days = cint(
			capkpi.db.get_single_value("System Settings", "force_user_to_reset_password")
		)

		if reset_pwd_after_days:
			last_password_reset_date = (
				capkpi.db.get_value("User", self.user, "last_password_reset_date") or today()
			)

			last_pwd_reset_days = date_diff(today(), last_password_reset_date)

			if last_pwd_reset_days > reset_pwd_after_days:
				return True

	def check_password(self, user, pwd):
		"""check password"""
		try:
			# returns user in correct case
			return check_password(user, pwd)
		except capkpi.AuthenticationError:
			self.fail("Incorrect password", user=user)

	def fail(self, message, user=None):
		if not user:
			user = _("Unknown User")
		capkpi.local.response["message"] = message
		add_authentication_log(message, user, status="Failed")
		capkpi.db.commit()
		raise capkpi.AuthenticationError

	def run_trigger(self, event="on_login"):
		for method in capkpi.get_hooks().get(event, []):
			capkpi.call(capkpi.get_attr(method), login_manager=self)

	def validate_hour(self):
		"""check if user is logging in during restricted hours"""
		login_before = int(capkpi.db.get_value("User", self.user, "login_before", ignore=True) or 0)
		login_after = int(capkpi.db.get_value("User", self.user, "login_after", ignore=True) or 0)

		if not (login_before or login_after):
			return

		from capkpi.utils import now_datetime

		current_hour = int(now_datetime().strftime("%H"))

		if login_before and current_hour > login_before:
			capkpi.throw(_("Login not allowed at this time"), capkpi.AuthenticationError)

		if login_after and current_hour < login_after:
			capkpi.throw(_("Login not allowed at this time"), capkpi.AuthenticationError)

	def login_as_guest(self):
		"""login as guest"""
		self.login_as("Guest")

	def login_as(self, user):
		self.user = user
		self.post_login()

	def logout(self, arg="", user=None):
		if not user:
			user = capkpi.session.user
		self.run_trigger("on_logout")

		if user == capkpi.session.user:
			delete_session(capkpi.session.sid, user=user, reason="User Manually Logged Out")
			self.clear_cookies()
		else:
			clear_sessions(user)

	def clear_cookies(self):
		clear_cookies()


class CookieManager:
	def __init__(self):
		self.cookies = {}
		self.to_delete = []

	def init_cookies(self):
		if not capkpi.local.session.get("sid"):
			return

		# sid expires in 3 days
		expires = datetime.datetime.now() + datetime.timedelta(days=3)
		if capkpi.session.sid:
			self.set_cookie("sid", capkpi.session.sid, expires=expires, httponly=True)
		if capkpi.session.session_country:
			self.set_cookie("country", capkpi.session.session_country)

	def set_cookie(self, key, value, expires=None, secure=False, httponly=False, samesite="Lax"):
		if not secure and hasattr(capkpi.local, "request"):
			secure = capkpi.local.request.scheme == "https"

		# Cordova does not work with Lax
		if capkpi.local.session.data.device == "mobile":
			samesite = None

		self.cookies[key] = {
			"value": value,
			"expires": expires,
			"secure": secure,
			"httponly": httponly,
			"samesite": samesite,
		}

	def delete_cookie(self, to_delete):
		if not isinstance(to_delete, (list, tuple)):
			to_delete = [to_delete]

		self.to_delete.extend(to_delete)

	def flush_cookies(self, response):
		for key, opts in self.cookies.items():
			response.set_cookie(
				key,
				quote((opts.get("value") or "").encode("utf-8")),
				expires=opts.get("expires"),
				secure=opts.get("secure"),
				httponly=opts.get("httponly"),
				samesite=opts.get("samesite"),
			)

		# expires yesterday!
		expires = datetime.datetime.now() + datetime.timedelta(days=-1)
		for key in set(self.to_delete):
			response.set_cookie(key, "", expires=expires)


@capkpi.whitelist()
def get_logged_user():
	return capkpi.session.user


def clear_cookies():
	if hasattr(capkpi.local, "session"):
		capkpi.session.sid = ""
	capkpi.local.cookie_manager.delete_cookie(
		["full_name", "user_id", "sid", "user_image", "system_user"]
	)


def validate_ip_address(user):
	"""check if IP Address is valid"""
	user = (
		capkpi.get_cached_doc("User", user) if not capkpi.flags.in_test else capkpi.get_doc("User", user)
	)
	ip_list = user.get_restricted_ip_list()
	if not ip_list:
		return

	system_settings = (
		capkpi.get_cached_doc("System Settings")
		if not capkpi.flags.in_test
		else capkpi.get_single("System Settings")
	)
	# check if bypass restrict ip is enabled for all users
	bypass_restrict_ip_check = system_settings.bypass_restrict_ip_check_if_2fa_enabled

	# check if two factor auth is enabled
	if system_settings.enable_two_factor_auth and not bypass_restrict_ip_check:
		# check if bypass restrict ip is enabled for login user
		bypass_restrict_ip_check = user.bypass_restrict_ip_check_if_2fa_enabled

	for ip in ip_list:
		if capkpi.local.request_ip.startswith(ip) or bypass_restrict_ip_check:
			return

	capkpi.throw(_("Access not allowed from this IP Address"), capkpi.AuthenticationError)


def get_login_attempt_tracker(user_name: str, raise_locked_exception: bool = True):
	"""Get login attempt tracker instance.

	:param user_name: Name of the loggedin user
	:param raise_locked_exception: If set, raises an exception incase of user not allowed to login
	"""
	sys_settings = capkpi.get_doc("System Settings")
	track_login_attempts = sys_settings.allow_consecutive_login_attempts > 0
	tracker_kwargs = {}

	if track_login_attempts:
		tracker_kwargs["lock_interval"] = sys_settings.allow_login_after_fail
		tracker_kwargs["max_consecutive_login_attempts"] = sys_settings.allow_consecutive_login_attempts

	tracker = LoginAttemptTracker(user_name, **tracker_kwargs)

	if raise_locked_exception and track_login_attempts and not tracker.is_user_allowed():
		capkpi.throw(
			_("Your account has been locked and will resume after {0} seconds").format(
				sys_settings.allow_login_after_fail
			),
			capkpi.SecurityException,
		)
	return tracker


class LoginAttemptTracker(object):
	"""Track login attemts of a user.

	Lock the account for s number of seconds if there have been n consecutive unsuccessful attempts to log in.
	"""

	def __init__(
		self, user_name: str, max_consecutive_login_attempts: int = 3, lock_interval: int = 5 * 60
	):
		"""Initialize the tracker.

		:param user_name: Name of the loggedin user
		:param max_consecutive_login_attempts: Maximum allowed consecutive failed login attempts
		:param lock_interval: Locking interval incase of maximum failed attempts
		"""
		self.user_name = user_name
		self.lock_interval = datetime.timedelta(seconds=lock_interval)
		self.max_failed_logins = max_consecutive_login_attempts

	@property
	def login_failed_count(self):
		return capkpi.cache().hget("login_failed_count", self.user_name)

	@login_failed_count.setter
	def login_failed_count(self, count):
		capkpi.cache().hset("login_failed_count", self.user_name, count)

	@login_failed_count.deleter
	def login_failed_count(self):
		capkpi.cache().hdel("login_failed_count", self.user_name)

	@property
	def login_failed_time(self):
		"""First failed login attempt time within lock interval.

		For every user we track only First failed login attempt time within lock interval of time.
		"""
		return capkpi.cache().hget("login_failed_time", self.user_name)

	@login_failed_time.setter
	def login_failed_time(self, timestamp):
		capkpi.cache().hset("login_failed_time", self.user_name, timestamp)

	@login_failed_time.deleter
	def login_failed_time(self):
		capkpi.cache().hdel("login_failed_time", self.user_name)

	def add_failure_attempt(self):
		"""Log user failure attempts into the system.

		Increase the failure count if new failure is with in current lock interval time period, if not reset the login failure count.
		"""
		login_failed_time = self.login_failed_time
		login_failed_count = self.login_failed_count  # Consecutive login failure count
		current_time = get_datetime()

		if not (login_failed_time and login_failed_count):
			login_failed_time, login_failed_count = current_time, 0

		if login_failed_time + self.lock_interval > current_time:
			login_failed_count += 1
		else:
			login_failed_time, login_failed_count = current_time, 1

		self.login_failed_time = login_failed_time
		self.login_failed_count = login_failed_count

	def add_success_attempt(self):
		"""Reset login failures."""
		del self.login_failed_count
		del self.login_failed_time

	def is_user_allowed(self) -> bool:
		"""Is user allowed to login

		User is not allowed to login if login failures are greater than threshold within in lock interval from first login failure.
		"""
		login_failed_time = self.login_failed_time
		login_failed_count = self.login_failed_count or 0
		current_time = get_datetime()

		if (
			login_failed_time
			and login_failed_time + self.lock_interval > current_time
			and login_failed_count > self.max_failed_logins
		):
			return False
		return True
