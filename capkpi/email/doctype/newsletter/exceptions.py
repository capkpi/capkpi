# Copyright (c) 2021, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See LICENSE

from capkpi.exceptions import ValidationError


class NewsletterAlreadySentError(ValidationError):
	pass


class NoRecipientFoundError(ValidationError):
	pass


class NewsletterNotSavedError(ValidationError):
	pass
