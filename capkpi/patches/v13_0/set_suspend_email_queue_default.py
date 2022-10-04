import capkpi
from capkpi.cache_manager import clear_defaults_cache


def execute():
	capkpi.db.set_default(
		"suspend_email_queue",
		capkpi.db.get_default("hold_queue", "Administrator") or 0,
		parent="__default",
	)

	capkpi.db.delete("DefaultValue", {"defkey": "hold_queue"})
	clear_defaults_cache()
