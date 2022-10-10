# -*- coding: utf-8 -*-
# Copyright (c) 2015, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import capkpi
from capkpi import _
from capkpi.model.document import Document


class OAuthProviderSettings(Document):
	pass


def get_oauth_settings():
	"""Returns oauth settings"""
	out = capkpi._dict(
		{
			"skip_authorization": capkpi.db.get_value("OAuth Provider Settings", None, "skip_authorization")
		}
	)

	return out
