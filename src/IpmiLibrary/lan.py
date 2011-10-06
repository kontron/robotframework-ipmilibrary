#
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
# author: Heiko Thiery <heiko.thiery@kontron.com>
#

import array

from robot.utils import asserts
import pyipmi

from utils import int_any_base
from mapping import *

class Lan:

    def get_lan_configuration_parameter(self, channel, parameter):
        """Get the LAN Configuration Parameter specified:

        `channel`
        `parameter`
        """

        channel = int_any_base(channel)
        parameter = find_lan_configuration_parameter(parameter)
        req = self.create_message_request('GetLanConfigurationParameters')
        req.command.channel_number = channel
        req.parameter_selector = parameter
        rsp = self.send_ipmi_message(req)
        return [c for c in rsp.data]

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

