# -*- coding: utf-8 -*-
# Copyright (c) 2015, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi import _
from capkpi.model.document import Document


class OAuthClient(Document):
	def validate(self):
		self.client_id = self.name
		if not self.client_secret:
			self.client_secret = capkpi.generate_hash(length=10)
		self.validate_grant_and_response()

	def validate_grant_and_response(self):
		if (
			self.grant_type == "Authorization Code"
			and self.response_type != "Code"
			or self.grant_type == "Implicit"
			and self.response_type != "Token"
		):
			capkpi.throw(
				_(
					"Combination of Grant Type (<code>{0}</code>) and Response Type (<code>{1}</code>) not allowed"
				).format(self.grant_type, self.response_type)
			)
