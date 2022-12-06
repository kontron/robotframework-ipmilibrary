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

from robot import utils
from robot.utils import asserts

from .mapping import *
from .utils import int_any_base

class Bmc:
    def issue_bmc_cold_reset(self):
        """Sends a _bmc cold reset_ to the given controler.
        """
        self._ipmi.cold_reset()

    def get_bmc_device_id(self):
        """Sends a _bmc get device id_ command to the given controller.
        """
        return self._ipmi.get_device_id()

    def product_id_should_be(self, product_id):
        """Fails if the GetDeviceID command response does not contain
        the given `device_id`.
        """
        product_id = int_any_base(product_id)
        device_id = self._ipmi.get_device_id()
        asserts.assert_equal(device_id.product_id, product_id)

    def manufacturer_id_should_be(self, manufacturer_id):
        """Fails if the GetDeviceID command response does not contain
        the given `manufacturer_id`.
        """
        manufacturer_id = int_any_base(manufacturer_id)
        device_id = self._ipmi.get_device_id()
        asserts.assert_equal(device_id.manufacturer_id, manufacturer_id)

    def device_should_support(self, supported_function, msg=None):
        """The device can support the following functions:
        'SENSOR', 'SDR_REPOSITORY', 'SEL', 'FRU_INVENTORY',
        'IPMB_EVENT_RECEIVER', 'IPMB_EVENT_GENERATOR', 'BRIDGE', 'CHASSIS'.
        """
        device_id = self._ipmi.get_device_id()
        supports = device_id.supports_function(supported_function)
        asserts.assert_equal(supports, True, msg=msg)

    def device_should_not_support(self, supported_function, msg=None):
        """The device can support the following functions:
        'SENSOR', 'SDR_REPOSITORY', 'SEL', 'FRU_INVENTORY',
        'IPMB_EVENT_RECEIVER', 'IPMB_EVENT_GENERATOR', 'BRIDGE', 'CHASSIS'.
        """
        device_id = self._ipmi.get_device_id()
        supports = device_id.supports_function(supported_function)
        asserts.assert_equal(supports, False, msg=msg)

    def i2c_write_read(self, bus_type, bus_id, channel, address, count, *data):
        """Sends a _Master Write-Read_ command to the given bus.
        """
        bus_type = int_any_base(bus_type)
        bus_id = int_any_base(bus_id)
        channel = int_any_base(channel)
        address = int_any_base(address)
        count = int_any_base(count)
        if isinstance(data, basestring):
            print('a', data)
            data = [int_any_base(d) for d in data.split(' ')]
        elif isinstance(data, tuple) or isinstance(data, list):
            print('b', data)
            data = [int_any_base(d) for d in data]
        else:
            print('c', data)
            data = [int_any_base(data)]
        data = array.array('B', data)
        rsp = self._ipmi.i2c_write_read(bus_type, bus_id, channel, address,
                count, data)
        return rsp

    def i2c_write(self, bus_type, bus_id, channel, address, *data):
        """Sends a _Master Write-Read_ command to the given bus.
        """
        self.i2c_write_read(bus_type, bus_id, channel, address, 0, data)

    def i2c_read(self, bus_type, bus_id, channel, address, count):
        """Sends a _Master Write-Read_ command to the given bus.
        """
        return self.i2c_write_read(bus_type, bus_id, channel, address, count, None)

    def start_watchdog_timer(self, value, action="Hard Reset",
            timer_use="SMS OS"):
        """Sets and starts IPMI watchdog timer.

        The watchdog is set to `value` and after that it is started.

        The maximum value is 6553 seconds. `value` is given in Robot
        Framework's time format (e.g. 1 minute 20 seconds) that is explained in
        the User Guide.

        `action` can be:
            No Action, Hard Reset, Power Down, Power Cycle
        `timer_use` can be:
            OEM, SMS OS, OS Load, BIOS Post, BIOS Frb2
        """

        timer_use = find_watchdog_timer_use(timer_use)
        config = pyipmi.bmc.Watchdog()
        config.timer_use = timer_use
        config.dont_stop = 1
        config.dont_log = 0
        config.pre_timeout_interval = 0
        config.pre_timeout_interrupt = 0
        config.timer_use_expiration_flags = 0xff
        # convert to 100ms
        config.initial_countdown = int(utils.timestr_to_secs(value) * 10)
        if (config.initial_countdown > 0xffff):
            raise RuntimeError('Watchdog value out of range')
        config.timeout_action = find_watchdog_action(action)
        # set watchdog
        self._ipmi.set_watchdog_timer(config)
        # start watchdog
        self._ipmi.reset_watchdog_timer()

    def reset_watchdog_timer(self):
        """Send the Reset Watchdog Timer Command
        """
        self._ipmi.reset_watchdog_timer()

    def stop_watchdog_timer(self, msg=None):
        """Stops the IPMI wachtdog timer.
        """

        config = pyipmi.bmc.Watchdog()
        config.timer_use = pyipmi.bmc.Watchdog.TIMER_USE_OEM
        config.dont_stop = 0
        config.dont_log = 0
        config.pre_timeout_interval = 0
        config.pre_timeout_interrupt = 0
        # 0xff means clear all expiration flags
        config.timer_use_expiration_flags = 0xff
        config.initial_countdown = 0
        config.timeout_action = pyipmi.bmc.Watchdog.TIMEOUT_ACTION_NO_ACTION
        self._ipmi.set_watchdog_timer(config)

    def get_watchdog_timer_countdown_value(self):
        """Returns the present watchdog countdown value."""
        config = self._ipmi.get_watchdog_timer()
        return config.present_countdown

    def watchdog_timeout_action_should_be(self, action, msg=None):
        """Fails if the IPMI Watchdog timeout action is not `action`
        `action` can be:
        No Action, Hard Reset, Power Down, Power Cycle
        """
        action = find_watchdog_action(action)
        config = self._ipmi.get_watchdog_timer()
        asserts.assert_equal(action, config.timeout_action, msg)

    def watchdog_timer_use_should_be(self, timer_use, msg=None):
        """Fails if the IPMI Watchdog timer use is not `timer_use`
        `timer_use` can be:
        OEM, SMS OS, OS Load, BIOS POST, BIOS FRB2
        """
        timer_use = find_watchdog_timer_use(timer_use)
        config = self._ipmi.get_watchdog_timer()
        asserts.assert_equal(timer_use, config.timer_use, msg)

    def watchdog_initial_timeout_value_should_be(self, value, msg=None):
        """
        """
        value = int_any_base(value)
        config = self._ipmi.get_watchdog_timer()
        asserts.assert_equal(value, config.initial_countdown, msg)

    def watchdog_should_be_started(self, msg=None):
        config = self._ipmi.get_watchdog_timer()
        asserts.assert_true(config.is_running, msg)

    def watchdog_should_be_stopped(self, msg=None):
        config = self._ipmi.get_watchdog_timer()
        asserts.assert_false(config.is_running, msg)
