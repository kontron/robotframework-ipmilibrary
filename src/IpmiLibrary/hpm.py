#
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
# author: Heiko Thiery <heiko.thiery@kontron.com>
#

from utils import int_any_base
from mapping import *


class Hpm:
    def hpm_start_firmware_upload(self, file_path, filename):
        """
        """
        cmd = 'hpm upgrade %s/%s all' % (file_path, filename)
        self._run_ipmitool_checked(cmd)

    def hpm_start_firmware_upload_and_activate(self, file_path, filename):
        """
        """
        cmd = 'hpm upgrade %s/%s activate all' % (file_path, filename)
        self._run_ipmitool_checked(cmd)

    def hpm_start_firmware_rollback(self):
        """
        """
        cmd = 'hpm rollback'
        self._run_ipmitool_checked(cmd)

    def hpm_get_component_property(self, component_name, property):
        """Return the component property.

        `component` is the description name of the component.
                    e.g.: "IPMC", "MMC", "Boot block"

        `property` can be the following:
                   "general properties",
                   "current version",
                   "description string",
                   "rollback version",
                   "deferred version"
        """
        comp_id = self._ipmi.find_component_id_by_descriptor(component_name)
        property_id = find_hpm_component_property(property)

        properties = self._ipmi.get_component_properties(comp_id)
        if property_id == pyipmi.hpm.PROPERTY_GENERAL_PROPERTIES:
            return properties.general_properties
        elif property_id == pyipmi.hpm.PROPERTY_CURRENT_VERSION:
            return properties.current_version.version_to_string()
        elif property_id == pyipmi.hpm.PROPERTY_DESCRIPTION_STRING:
            return properties.description
        elif property_id == pyipmi.hpm.PROPERTY_ROLLBACK_VERSION:
            return properties.rollback_version.version_to_string()
        elif property_id == pyipmi.hpm.PROPERTY_DEFERRED_VERSION:
            return properties.deferred_version.version_to_string()
