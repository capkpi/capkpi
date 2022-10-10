# Copyright (c) 2017, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import print_function, unicode_literals

import capkpi


@capkpi.whitelist()
def get_leaderboard_config():
	leaderboard_config = capkpi._dict()
	leaderboard_hooks = capkpi.get_hooks("leaderboards")
	for hook in leaderboard_hooks:
		leaderboard_config.update(capkpi.get_attr(hook)())

	return leaderboard_config
