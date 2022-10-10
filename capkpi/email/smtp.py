# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import email.utils
import smtplib
import sys

import _socket

import capkpi
from capkpi import _
from capkpi.utils import cint, cstr, parse_addr


def send(email, append_to=None, retry=1):
	"""Deprecated: Send the message or add it to Outbox Email"""

	def _send(retry):
		try:
			smtpserver = SMTPServer(append_to=append_to)

			# validate is called in as_string
			email_body = email.as_string()

			smtpserver.sess.sendmail(email.sender, email.recipients + (email.cc or []), email_body)
		except smtplib.SMTPSenderRefused:
			capkpi.throw(_("Invalid login or password"), title="Email Failed")
			raise
		except smtplib.SMTPRecipientsRefused:
			capkpi.msgprint(_("Invalid recipient address"), title="Email Failed")
			raise
		except (smtplib.SMTPServerDisconnected, smtplib.SMTPAuthenticationError):
			if not retry:
				raise
			else:
				retry = retry - 1
				_send(retry)

	_send(retry)


def get_outgoing_email_account(raise_exception_not_set=True, append_to=None, sender=None):
	"""Returns outgoing email account based on `append_to` or the default
	outgoing account. If default outgoing account is not found, it will
	try getting settings from `site_config.json`."""

	sender_email_id = None
	_email_account = None

	if sender:
		sender_email_id = parse_addr(sender)[1]

	if not getattr(capkpi.local, "outgoing_email_account", None):
		capkpi.local.outgoing_email_account = {}

	if not (
		capkpi.local.outgoing_email_account.get(append_to)
		or capkpi.local.outgoing_email_account.get(sender_email_id)
		or capkpi.local.outgoing_email_account.get("default")
	):
		email_account = None

		if sender_email_id:
			# check if the sender has an email account with enable_outgoing
			email_account = _get_email_account({"enable_outgoing": 1, "email_id": sender_email_id})

		if not email_account and append_to:
			# append_to is only valid when enable_incoming is checked
			email_accounts = capkpi.db.get_values(
				"Email Account",
				{
					"enable_outgoing": 1,
					"enable_incoming": 1,
					"append_to": append_to,
				},
				cache=True,
			)

			if email_accounts:
				_email_account = email_accounts[0]

			else:
				email_account = _get_email_account(
					{"enable_outgoing": 1, "enable_incoming": 1, "append_to": append_to}
				)

		if not email_account:
			# sender don't have the outging email account
			sender_email_id = None
			email_account = get_default_outgoing_email_account(
				raise_exception_not_set=raise_exception_not_set
			)

		if not email_account and _email_account:
			# if default email account is not configured then setup first email account based on append to
			email_account = _email_account

		if (
			not email_account
			and raise_exception_not_set
			and cint(capkpi.db.get_single_value("System Settings", "setup_complete"))
		):
			capkpi.throw(
				_("Please setup default Email Account from Setup > Email > Email Account"),
				capkpi.OutgoingEmailError,
			)

		if email_account:
			if email_account.enable_outgoing and not getattr(email_account, "from_site_config", False):
				raise_exception = True
				if (
					email_account.smtp_server in ["localhost", "127.0.0.1"]
					or email_account.no_smtp_authentication
				):
					raise_exception = False
				email_account.password = email_account.get_password(raise_exception=raise_exception)
			email_account.default_sender = email.utils.formataddr(
				(email_account.name, email_account.get("email_id"))
			)

		capkpi.local.outgoing_email_account[append_to or sender_email_id or "default"] = email_account

	return (
		capkpi.local.outgoing_email_account.get(append_to)
		or capkpi.local.outgoing_email_account.get(sender_email_id)
		or capkpi.local.outgoing_email_account.get("default")
	)


def get_default_outgoing_email_account(raise_exception_not_set=True):
	"""conf should be like:
	{
	 "mail_server": "smtp.example.com",
	 "mail_port": 587,
	 "use_tls": 1,
	 "mail_login": "emails@example.com",
	 "mail_password": "Super.Secret.Password",
	 "auto_email_id": "emails@example.com",
	 "email_sender_name": "Example Notifications",
	 "always_use_account_email_id_as_sender": 0,
	 "always_use_account_name_as_sender_name": 0
	}
	"""
	email_account = _get_email_account({"enable_outgoing": 1, "default_outgoing": 1})
	if email_account:
		email_account.password = email_account.get_password(raise_exception=False)

	if not email_account and capkpi.conf.get("mail_server"):
		# from site_config.json
		email_account = capkpi.new_doc("Email Account")
		email_account.update(
			{
				"smtp_server": capkpi.conf.get("mail_server"),
				"smtp_port": capkpi.conf.get("mail_port"),
				# legacy: use_ssl was used in site_config instead of use_tls, but meant the same thing
				"use_tls": cint(capkpi.conf.get("use_tls") or 0) or cint(capkpi.conf.get("use_ssl") or 0),
				"login_id": capkpi.conf.get("mail_login"),
				"email_id": capkpi.conf.get("auto_email_id")
				or capkpi.conf.get("mail_login")
				or "notifications@example.com",
				"password": capkpi.conf.get("mail_password"),
				"always_use_account_email_id_as_sender": capkpi.conf.get(
					"always_use_account_email_id_as_sender", 0
				),
				"always_use_account_name_as_sender_name": capkpi.conf.get(
					"always_use_account_name_as_sender_name", 0
				),
			}
		)
		email_account.from_site_config = True
		email_account.name = capkpi.conf.get("email_sender_name") or "CapKPI"

	if not email_account and not raise_exception_not_set:
		return None

	if capkpi.are_emails_muted():
		# create a stub
		email_account = capkpi.new_doc("Email Account")
		email_account.update({"email_id": "notifications@example.com"})

	return email_account


def _get_email_account(filters):
	name = capkpi.db.get_value("Email Account", filters)
	return capkpi.get_doc("Email Account", name) if name else None


class SMTPServer:
	def __init__(
		self,
		login=None,
		password=None,
		server=None,
		port=None,
		use_tls=None,
		use_ssl=None,
		append_to=None,
	):
		# get defaults from mail settings

		self._sess = None
		self.email_account = None
		self.server = None
		self.append_emails_to_sent_folder = None

		if server:
			self.server = server
			self.port = port
			self.use_tls = cint(use_tls)
			self.use_ssl = cint(use_ssl)
			self.login = login
			self.password = password

		else:
			self.setup_email_account(append_to)

	def setup_email_account(self, append_to=None, sender=None):
		self.email_account = get_outgoing_email_account(
			raise_exception_not_set=False, append_to=append_to, sender=sender
		)
		if self.email_account:
			self.server = self.email_account.smtp_server
			self.login = getattr(self.email_account, "login_id", None) or self.email_account.email_id
			if not self.email_account.no_smtp_authentication:
				if self.email_account.ascii_encode_password:
					self.password = capkpi.safe_encode(self.email_account.password, "ascii")
				else:
					self.password = self.email_account.password
			else:
				self.password = None
			self.port = self.email_account.smtp_port
			self.use_tls = self.email_account.use_tls
			self.sender = self.email_account.email_id
			self.use_ssl = self.email_account.use_ssl_for_outgoing
			self.append_emails_to_sent_folder = self.email_account.append_emails_to_sent_folder
			self.always_use_account_email_id_as_sender = cint(
				self.email_account.get("always_use_account_email_id_as_sender")
			)
			self.always_use_account_name_as_sender_name = cint(
				self.email_account.get("always_use_account_name_as_sender_name")
			)

	@property
	def sess(self):
		"""get session"""
		if self._sess:
			return self._sess

		# check if email server specified
		if not getattr(self, "server"):
			err_msg = _(
				"Email Account not setup. Please create a new Email Account from Setup > Email > Email Account"
			)
			capkpi.msgprint(err_msg)
			raise capkpi.OutgoingEmailError(err_msg)

		try:
			if self.use_ssl:
				if not self.port:
					self.port = 465

				self._sess = smtplib.SMTP_SSL((self.server or ""), cint(self.port))
			else:
				if self.use_tls and not self.port:
					self.port = 587

				self._sess = smtplib.SMTP(cstr(self.server or ""), cint(self.port) or None)

			if not self._sess:
				err_msg = _("Could not connect to outgoing email server")
				capkpi.msgprint(err_msg)
				raise capkpi.OutgoingEmailError(err_msg)

			if self.use_tls:
				self._sess.ehlo()
				self._sess.starttls()
				self._sess.ehlo()

			if self.login and self.password:
				ret = self._sess.login(str(self.login or ""), str(self.password or ""))

				# check if logged correctly
				if ret[0] != 235:
					capkpi.msgprint(ret[1])
					raise capkpi.OutgoingEmailError(ret[1])

			return self._sess

		except smtplib.SMTPAuthenticationError as e:
			from capkpi.email.doctype.email_account.email_account import EmailAccount

			EmailAccount.throw_invalid_credentials_exception()

		except _socket.error as e:
			# Invalid mail server -- due to refusing connection
			capkpi.throw(
				_("Invalid Outgoing Mail Server or Port"),
				exc=capkpi.ValidationError,
				title=_("Incorrect Configuration"),
			)

		except smtplib.SMTPException:
			capkpi.msgprint(_("Unable to send emails at this time"))
			raise
