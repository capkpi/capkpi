# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import base64
import json

import jwt
from six import string_types

import capkpi
import capkpi.utils
from capkpi import _
from capkpi.utils.password import get_decrypted_password


class SignupDisabledError(capkpi.PermissionError):
	pass


def get_oauth2_providers():
	out = {}
	providers = capkpi.get_all("Social Login Key", fields=["*"])
	for provider in providers:
		authorize_url, access_token_url = provider.authorize_url, provider.access_token_url
		if provider.custom_base_url:
			authorize_url = provider.base_url + provider.authorize_url
			access_token_url = provider.base_url + provider.access_token_url
		out[provider.name] = {
			"flow_params": {
				"name": provider.name,
				"authorize_url": authorize_url,
				"access_token_url": access_token_url,
				"base_url": provider.base_url,
			},
			"redirect_uri": provider.redirect_url,
			"api_endpoint": provider.api_endpoint,
		}
		if provider.auth_url_data:
			out[provider.name]["auth_url_data"] = json.loads(provider.auth_url_data)

		if provider.api_endpoint_args:
			out[provider.name]["api_endpoint_args"] = json.loads(provider.api_endpoint_args)

	return out


def get_oauth_keys(provider):
	"""get client_id and client_secret from database or conf"""

	# try conf
	keys = capkpi.conf.get("{provider}_login".format(provider=provider))

	if not keys:
		# try database
		client_id, client_secret = capkpi.get_value(
			"Social Login Key", provider, ["client_id", "client_secret"]
		)
		client_secret = get_decrypted_password("Social Login Key", provider, "client_secret")
		keys = {"client_id": client_id, "client_secret": client_secret}
		return keys
	else:
		return {"client_id": keys["client_id"], "client_secret": keys["client_secret"]}


def get_oauth2_authorize_url(provider, redirect_to):
	flow = get_oauth2_flow(provider)

	state = {
		"site": capkpi.utils.get_url(),
		"token": capkpi.generate_hash(),
		"redirect_to": redirect_to,
	}

	# relative to absolute url
	data = {
		"redirect_uri": get_redirect_uri(provider),
		"state": base64.b64encode(bytes(json.dumps(state).encode("utf-8"))),
	}

	oauth2_providers = get_oauth2_providers()

	# additional data if any
	data.update(oauth2_providers[provider].get("auth_url_data", {}))

	return flow.get_authorize_url(**data)


def get_oauth2_flow(provider):
	from rauth import OAuth2Service

	# get client_id and client_secret
	params = get_oauth_keys(provider)

	oauth2_providers = get_oauth2_providers()

	# additional params for getting the flow
	params.update(oauth2_providers[provider]["flow_params"])

	# and we have setup the communication lines
	return OAuth2Service(**params)


def get_redirect_uri(provider):
	keys = capkpi.conf.get("{provider}_login".format(provider=provider))

	if keys and keys.get("redirect_uri"):
		# this should be a fully qualified redirect uri
		return keys["redirect_uri"]

	else:
		oauth2_providers = get_oauth2_providers()

		redirect_uri = oauth2_providers[provider]["redirect_uri"]

		# this uses the site's url + the relative redirect uri
		return capkpi.utils.get_url(redirect_uri)


def login_via_oauth2(provider, code, state, decoder=None):
	info = get_info_via_oauth(provider, code, decoder)
	login_oauth_user(info, provider=provider, state=state)


def login_via_oauth2_id_token(provider, code, state, decoder=None):
	info = get_info_via_oauth(provider, code, decoder, id_token=True)
	login_oauth_user(info, provider=provider, state=state)


def get_info_via_oauth(provider, code, decoder=None, id_token=False):
	flow = get_oauth2_flow(provider)
	oauth2_providers = get_oauth2_providers()

	args = {
		"data": {
			"code": code,
			"redirect_uri": get_redirect_uri(provider),
			"grant_type": "authorization_code",
		}
	}

	if decoder:
		args["decoder"] = decoder

	session = flow.get_auth_session(**args)

	if id_token:
		parsed_access = json.loads(session.access_token_response.text)

		token = parsed_access["id_token"]

		info = jwt.decode(token, flow.client_secret, verify=False)
	else:
		api_endpoint = oauth2_providers[provider].get("api_endpoint")
		api_endpoint_args = oauth2_providers[provider].get("api_endpoint_args")
		info = session.get(api_endpoint, params=api_endpoint_args).json()

	if not (info.get("email_verified") or info.get("email")):
		capkpi.throw(_("Email not verified with {0}").format(provider.title()))

	return info


def login_oauth_user(
	data=None, provider=None, state=None, email_id=None, key=None, generate_login_token=False
):
	# NOTE: This could lead to security issue as the signed in user can type any email address in complete_signup
	# if email_id and key:
	# 	data = json.loads(capkpi.db.get_temp(key))
	# 	# What if data is missing because of an invalid key
	# 	data["email"] = email_id
	#
	# elif not (data.get("email") and get_first_name(data)) and not capkpi.db.exists("User", data.get("email")):
	# 	# ask for user email
	# 	key = capkpi.db.set_temp(json.dumps(data))
	# 	capkpi.db.commit()
	# 	capkpi.local.response["type"] = "redirect"
	# 	capkpi.local.response["location"] = "/complete_signup?key=" + key
	# 	return

	# json.loads data and state
	if isinstance(data, string_types):
		data = json.loads(data)

	if isinstance(state, string_types):
		state = base64.b64decode(state)
		state = json.loads(state.decode("utf-8"))

	if not (state and state["token"]):
		capkpi.respond_as_web_page(_("Invalid Request"), _("Token is missing"), http_status_code=417)
		return

	user = get_email(data)

	if not user:
		capkpi.respond_as_web_page(
			_("Invalid Request"), _("Please ensure that your profile has an email address")
		)
		return

	try:
		if update_oauth_user(user, data, provider) is False:
			return

	except SignupDisabledError:
		return capkpi.respond_as_web_page(
			"Signup is Disabled",
			"Sorry. Signup from Website is disabled.",
			success=False,
			http_status_code=403,
		)

	capkpi.local.login_manager.user = user
	capkpi.local.login_manager.post_login()

	# because of a GET request!
	capkpi.db.commit()

	if capkpi.utils.cint(generate_login_token):
		login_token = capkpi.generate_hash(length=32)
		capkpi.cache().set_value(
			"login_token:{0}".format(login_token), capkpi.local.session.sid, expires_in_sec=120
		)

		capkpi.response["login_token"] = login_token

	else:
		redirect_to = state.get("redirect_to")
		redirect_post_login(
			desk_user=capkpi.local.response.get("message") == "Logged In",
			redirect_to=redirect_to,
			provider=provider,
		)


def update_oauth_user(user, data, provider):
	if isinstance(data.get("location"), dict):
		data["location"] = data.get("location").get("name")

	save = False

	if not capkpi.db.exists("User", user):

		# is signup disabled?
		if capkpi.utils.cint(capkpi.db.get_single_value("Website Settings", "disable_signup")):
			raise SignupDisabledError

		save = True
		user = capkpi.new_doc("User")

		gender = data.get("gender", "").title()

		if gender and not capkpi.db.exists("Gender", gender):
			doc = capkpi.new_doc("Gender", {"gender": gender})
			doc.insert(ignore_permissions=True)

		user.update(
			{
				"doctype": "User",
				"first_name": get_first_name(data),
				"last_name": get_last_name(data),
				"email": get_email(data),
				"gender": gender,
				"enabled": 1,
				"new_password": capkpi.generate_hash(get_email(data)),
				"location": data.get("location"),
				"user_type": "Website User",
				"user_image": data.get("picture") or data.get("avatar_url"),
			}
		)

	else:
		user = capkpi.get_doc("User", user)
		if not user.enabled:
			capkpi.respond_as_web_page(_("Not Allowed"), _("User {0} is disabled").format(user.email))
			return False

	if provider == "facebook" and not user.get_social_login_userid(provider):
		save = True
		user.set_social_login_userid(provider, userid=data["id"], username=data.get("username"))
		user.update({"user_image": "https://graph.facebook.com/{id}/picture".format(id=data["id"])})

	elif provider == "google" and not user.get_social_login_userid(provider):
		save = True
		user.set_social_login_userid(provider, userid=data["id"])

	elif provider == "github" and not user.get_social_login_userid(provider):
		save = True
		user.set_social_login_userid(provider, userid=data["id"], username=data.get("login"))

	elif provider == "capkpi" and not user.get_social_login_userid(provider):
		save = True
		user.set_social_login_userid(provider, userid=data["sub"])

	elif provider == "office_365" and not user.get_social_login_userid(provider):
		save = True
		user.set_social_login_userid(provider, userid=data["sub"])

	elif provider == "salesforce" and not user.get_social_login_userid(provider):
		save = True
		user.set_social_login_userid(provider, userid="/".join(data["sub"].split("/")[-2:]))

	elif not user.get_social_login_userid(provider):
		save = True
		user_id_property = capkpi.db.get_value("Social Login Key", provider, "user_id_property") or "sub"
		user.set_social_login_userid(provider, userid=data[user_id_property])

	if save:
		user.flags.ignore_permissions = True
		user.flags.no_welcome_mail = True

		# set default signup role as per Portal Settings
		default_role = capkpi.db.get_single_value("Portal Settings", "default_role")
		if default_role:
			user.add_roles(default_role)

		user.save()


def get_first_name(data):
	return data.get("first_name") or data.get("given_name") or data.get("name")


def get_last_name(data):
	return data.get("last_name") or data.get("family_name")


def get_email(data):
	return data.get("email") or data.get("upn") or data.get("unique_name")


def redirect_post_login(desk_user, redirect_to=None, provider=None):
	# redirect!
	capkpi.local.response["type"] = "redirect"

	if not redirect_to:
		# the #desktop is added to prevent a facebook redirect bug
		desk_uri = "/app/workspace" if provider == "facebook" else "/app"
		redirect_to = desk_uri if desk_user else "/me"
		redirect_to = capkpi.utils.get_url(redirect_to)

	capkpi.local.response["location"] = redirect_to
