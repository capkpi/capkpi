# imports - standard imports
import sys

# imports - module imports
from capkpi.integrations.capkpi_providers.capkpicloud import capkpicloud_migrator


def migrate_to(local_site, capkpi_provider):
	if capkpi_provider in ("capkpi.cloud", "capkpicloud.com"):
		return capkpicloud_migrator(local_site)
	else:
		print("{} is not supported yet".format(capkpi_provider))
		sys.exit(1)
