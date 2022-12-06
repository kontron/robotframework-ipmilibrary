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

import array

from robot.utils import asserts
import pyipmi

#import utils
from .utils import int_any_base
from .mapping import *

class Lan:

    def get_lan_configuration_parameter(self, channel, parameter):
        """Get the LAN Configuration Parameter specified:

        `channel`
        `parameter` - following parameters are supporte:

        SET_IN_PROGRESS
        AUTHENTICATION_TYPE_SUPPORT
        AUTHENTICATION_TYPE_ENABLE
        IP_ADDRESS
        IP_ADDRESS_SOURCE
        MAC_ADDRESS
        SUBNET_MASK
        IPV4_HEADER_PARAMETERS
        PRIMARY_RMCP_PORT
        SECONDARY_RMCP_PORT
        BMC_GENERATED_ARP_CONTROL
        GRATUITOUS_ARP_INTERVAL
        DEFAULT_GATEWAY_ADDRESS
        DEFAULT_GATEWAY_MAC_ADDRESS
        BACKUP_GATEWAY_ADDRESS
        BACKUP_GATEWAY_MAC_ADDRESS
        COMMUNITY_STRING
        NUMBER_OF_DESTINATIONS
        DESTINATION_TYPE
        DESTINATION_ADDRESSES
        802_1Q_VLAN_ID
        802_1Q_VLAN_PRIORITY
        RMCP_PLUS_MESSAGING_CIPHER_SUITE_ENTRY_SUPPORT
        RMCP_PLUS__MESSAGING_CIPHER_SUITE_ENTRIES
        RMCP_PLUS_MESSAGING_CIPHER_SUITE_PRIVILEGE_LEVES
        DESTINATION_ADDRESS_VLAN_TAGS
        """

        channel = int_any_base(channel)
        parameter = find_lan_configuration_parameter(parameter)
        data = self._ipmi.get_lan_configuration_parameters(channel, parameter_selector=parameter)
        return [c for c in data]

    def set_lan_configuration_parameter(self, channel, parameter, data):
        """Set the LAN Configuration Parameter specified:

        `channel`
        `parameterr`
        `data`

        Example:
        | Set Lan Configuraion Parameter | 1 | IP Address | 10 10 10 10 |
        | # read value first
        | ${oldValue}= | Get Lan Configuration Parameter | 1 | IP Address |
        | Set Lan Configuraion Parameter | 1 | IP Address | ${oldValue} |
        """

        channel = int_any_base(channel)
        parameter = find_lan_configuration_parameter(parameter)
        if isinstance(data, basestring):
            data = [int_any_base(d) for d in data.split(' ')]

        data = array.array('c', [chr(c) for c in data])
        req = self.create_message_request('SetLanConfigurationParameters')
        req.command.channel_number = channel
        req.parameter_selector = parameter
        req.data = data
        rsp = self.send_ipmi_message(req)

    def get_lan_interface_ip_address_source(self, channel):
        """Get LAN Interface IP address source parameter for the channel.

        `channel`
        """

        source = self.get_lan_configuration_parameter(channel,
                pyipmi.lan.LAN_PARAMETER_IP_ADDRESS_SOURCE)
        return source[0]

    def set_lan_interface_ip_address_source(self, channel, source):
        """Set LAN Interface IP address source parameter:

        `channel`
        `source`

        The following sources are supported:
        UNSPECIFIED, STATIC, DHCP, BIOS_OR_SYSTEM_INTERFACE, BMC_OTHER_PROTOCOL
        """

        channel = int_any_base(channel)
        source = find_lan_ip_source(source)

        self.set_lan_configuration_parameter(channel,
                pyipmi.lan.LAN_PARAMETER_IP_ADDRESS_SOURCE, (source, ))

    def get_lan_interface_ip_address(self, channel):
        """Get IP address for the channel.

        `channel`
        """

        ip = self.get_lan_configuration_parameter(channel,
                pyipmi.lan.LAN_PARAMETER_IP_ADDRESS)
        return misc.ip_address_to_string(ip)

    def set_lan_interface_ip_address(self, channel, ip_address):
        """Set IP address for the channel.

        `channel`
        """

        channel = int_any_base(channel)
        ip_address = misc.parse_ip_address(ip_address)
        self.set_lan_configuration_parameter(channel,
                pyipmi.lan.LAN_PARAMETER_IP_ADDRESS, ip_address)

    def get_lan_interface_mac_address(self, channel):
        """Get MAC address for the channel.

        `channel`
        """

        channel = int_any_base(channel)
        mac = self.get_lan_configuration_parameter(channel,
                pyipmi.lan.LAN_PARAMETER_MAC_ADDRESS)
        return misc.mac_address_to_string(mac)

    def set_lan_interface_mac_address(self, channel, mac_address):
        """Set MAC address for the channel.

        `channel`
        `mac_address`
        """

        channel = int_any_base(channel)
        mac_address = misc.parse_mac_address(mac_address)
        self.set_lan_configuration_parameter(channel,
                pyipmi.lan.LAN_PARAMETER_MAC_ADDRESS, mac_address)

    def get_lan_interface_gateway_ip_address(self, channel):
        """Get IP address for the channel.

        `channel`
        """

        ip = self.get_lan_configuration_parameter(channel,
                pyipmi.lan.LAN_PARAMETER_DEFAULT_GATEWAY_ADDRESS)
        return misc.ip_address_to_string(ip)

    def set_lan_interface_gateway_ip_address(self, channel, ip_address):
        """Set the IP address of the interface channel.

        `channel`
        """

        channel = int_any_base(channel)
        ip_address = misc.parse_ip_address(ip_address)
        self.set_lan_configuration_parameter(channel,
                pyipmi.lan.LAN_PARAMETER_DEFAULT_GATEWAY_ADDRESS, ip_address)

    def get_lan_interface_gateway_mac_address(self, channel):
        """Get LAN Interface gateway MAC address parameter for the channel.

        `channel`
        """

        mac = self.get_lan_configuration_parameter(channel,
                pyipmi.lan.LAN_PARAMETER_DEFAULT_GATEWAY_MAC_ADDRESS)
        return misc.mac_address_to_string(mac, inverted=False)

    def set_lan_interface_gateway_mac_address(self, channel, mac_address):
        """Set the MAC address of the interface channel's gateway.

        `channel`
        """

        channel = int_any_base(channel)
        mac_address = misc.parse_mac_address(mac_address)
        mac_address = [b for b in reversed(mac_address)]
        self.set_lan_configuration_parameter(channel,
                pyipmi.lan.LAN_PARAMETER_DEFAULT_GATEWAY_MAC_ADDRESS,
                        mac_address)
