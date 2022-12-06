# Copyright 2014 Kontron Europe GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from robot.utils import asserts
from robot import utils
from pyipmi.errors import DataNotFound, CompletionCodeError

from .utils import int_any_base
from .mapping import *


class Hpm:
    def hpm_start_firmware_upload(self, file_path, filename):
        """*DEPRECATED*"""
        cmd = 'hpm upgrade %s/%s all' % (file_path, filename)
        self._run_ipmitool_checked(cmd)

    def hpm_start_firmware_upload_and_activate(self, file_path, filename):
        """*DEPRECATED*"""
        cmd = 'hpm upgrade %s/%s activate all' % (file_path, filename)
        self._run_ipmitool_checked(cmd)

    def hpm_start_firmware_rollback(self):
        """*DEPRECATED*"""
        cmd = 'hpm rollback'
        self._run_ipmitool_checked(cmd)


    def hpm_install_component_from_file(self, filename, component_name):
        """ Install the specified component
        """

        id = self._ipmi.find_component_id_by_descriptor(component_name)
        self._ipmi.install_component_from_file(filename, id)


    def hpm_open_upgrade_image(self, filename):
        """
        """
        image = self._ipmi.open_upgrade_image(filename)
        return image

    def hpm_image_header_value_should_be(self, filename, field, expected_value):
        """
        """
        image = self._ipmi.load_upgrade_image(filename)

        value = getattr(image.header, field)
        asserts.assert_equal(expected_value, value)

    def hpm_get_image_upgrade_version(self, filename):
        version = self._ipmi.get_upgrade_version_from_file(filename)
        return version.version_to_string()

    def hpm_get_target_upgrade_capabilities(self):
        """
        """
        return self._ipmi.get_target_upgrade_capabilities()

    def hpm_get_component_property(self, component_name, property):
        """Return the component property as string.

        `component_name` is the description name of the component.
                    e.g.: "IPMC", "MMC", "Boot block"

        `property` can be the following:
                   "general properties",
                   "current version",
                   "description string",
                   "rollback version",
                   "deferred version"
        """

        property_id = find_hpm_component_property(property)

        comp_id = self._ipmi.find_component_id_by_descriptor(component_name)

        if comp_id is None:
            raise DataNotFound('no component with name %s found' % component_name)

        property = self._ipmi.get_component_property(comp_id, property_id)

        if property_id == pyipmi.hpm.PROPERTY_GENERAL_PROPERTIES:
            return property.general

        elif property_id == pyipmi.hpm.PROPERTY_CURRENT_VERSION:
            return property.version.version_to_string()

        elif property_id == pyipmi.hpm.PROPERTY_DESCRIPTION_STRING:
            return property.description

        elif property_id == pyipmi.hpm.PROPERTY_ROLLBACK_VERSION:
            return property.version.version_to_string()

        elif property_id == pyipmi.hpm.PROPERTY_DEFERRED_VERSION:
            return property.version.version_to_string()

    def hpm_get_upgrade_status(self):
        """
        """
        return self._ipmi.get_upgrade_status()

    def hpm_activate_firmware(self, override=None):
        """
        """
        return self._ipmi.activate_firmware_and_wait(timeout=10)

    def hpm_abort_firmware_upgrade(self):
        """
        """
        return self._ipmi.abort_firmware_upgrade()

    def hpm_initiate_upgrade_action(self, component_name, action,
            expected_cc=pyipmi.msgs.constants.CC_OK):
        """
        component_name: Other than the raw command here is only one
                        component allowed. e.g. MMC, IPMC,

        action:
            BACKUP_COMPONENT,
            PREPARE_COMPONENT,
            UPLOAD_FOR_UPGRADE,
            UPLOAD_FOR_COMPARE
        """
        id = self._ipmi.find_component_id_by_descriptor(component_name)
        action = find_hpm_upgrade_action(action)
        expected_cc = int_any_base(expected_cc)

        try:
            self._ipmi.initiate_upgrade_action(1 << id, action)
        except CompletionCodeError as e:
            if e.cc == expected_cc:
                pass
            else:
                raise CompletionCodeError(e.cc)

    def hpm_upload_firmware_binary(self, binary):
        self._ipmi.upload_binary(binary)

    def hpm_finish_firmware_upload(self, component_name, size,
            expected_cc=pyipmi.msgs.constants.CC_OK):
        size = int_any_base(size)
        id = self._ipmi.find_component_id_by_descriptor(component_name)
        expected_cc = int_any_base(expected_cc)
        if id is None:
            raise AssertionError('component_name=%s not found' % (component_name))

        try:
            self._ipmi.finish_firmware_upload(id, size)
        except CompletionCodeError as e:
            if e.cc == expected_cc:
                pass
            else:
                raise CompletionCodeError(e.cc)

    def hpm_wait_until_long_duration_command_is_finished(self, cmd,
            timeout, interval):
        cmd = int_any_base(cmd)
        timeout = utils.timestr_to_secs(timeout)
        interval = utils.timestr_to_secs(interval)
        self._ipmi.wait_for_long_duration_command(cmd, timeout, interval)

    def hpm_query_selftest_results(self):
        return self._ipmi.query_selftest_results()

    def hpm_query_rollback_status(self):
        return self._ipmi.query_rollback_status()

    def hpm_initiate_manual_rollback(self):
        return self._ipmi.initiate_manual_rollback_and_wait()
