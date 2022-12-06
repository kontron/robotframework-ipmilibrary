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

import struct
import time

from robot import utils
from robot.utils import asserts

from .utils import int_any_base
from .mapping import *


class NotSupportedError(Exception):
    pass

class Sel:
    @property
    def _sel_records(self):
        if 'prefetched_sel_records' in self._cp:
            return self._cp['prefetched_sel_records']
        else:
            return self._ipmi.get_sel_entries()

    @property
    def _selected_sel_record(self):
        try:
            return self._cp['selected_sel_record']
        except KeyError:
            AssertionError('No SEL record selected.')

    @_selected_sel_record.setter
    def _selected_sel_record(self, value):
        self._cp['selected_sel_record'] = value

    def _invalidate_prefetched_sel_records(self):
        if 'prefetched_sel_records' in self._cp:
            del self._cp['prefetched_sel_records']

    def prefetch_sel(self):
        """Prefetches the sensor event log.

        Fetching the SEL is required for all further operation on the SEL.

        See `Sel Should Contain X Times Sensor Type`, `Select Sel Record By
        Sensor Type` and `Wait Until Sel Contains Sensor Type`.
        """

        self._info('Prefetching SEL')
        self._invalidate_prefetched_sel_records()
        self._cp['prefetched_sel_records'] = self._ipmi.get_sel_entries()

    def clear_sel(self):
        """Clears the sensor event log."""
        self._invalidate_prefetched_sel_records()
        self._ipmi.clear_sel()

    def get_sel_entries_count(self):
        """Returns the number of entries in SEL."""
        return self._ipmi.get_sel_entries_count()

    def log_sel(self):
        """Dumps the sensor event log and logs it."""

        print('*INFO* SEL')
        for record in self._sel_records:
            print(record)

    def _find_sel_records_by_sensor_type(self, type):
        matches = []
        for record in self._sel_records:
            if record.sensor_type == type:
                matches.append(record)
        return matches

    def _find_sel_records_by_sensor_number(self, number):
        matches = []
        for record in self._sel_records:
            if record.sensor_number == number:
                matches.append(record)
        return matches

    def sel_should_contain_x_entries(self, count, msg=None):
        """Fails if the SEL does not contain `count` entries.
        """
        count = int(count)
        asserts.assert_equal(count, len(self._sel_records), msg)

    def sel_should_contain_x_times_sensor_type(self, type, count, msg=None):
        """Fails if the SEL does not contain `count` times an event with the
        given sensor type.
        """

        type = find_sensor_type(type)
        count = int(count)

        records = self._find_sel_records_by_sensor_type(type)
        asserts.assert_equal(count, len(records), msg)

    def sel_should_contain_sensor_type(self, type, msg=None):
        """Fails if SEL contains the given sensor type.
        """

        type = find_sensor_type(type)
        records = self._find_sel_records_by_sensor_type(type)
        if len(records) == 0:
            raise AssertionError('SEL doesn`t contain sensor type %s' % type)

    def sel_should_not_contain_sensor_type(self, type, msg=None):
        """Fails if SEL contains the given sensor type.
        """

        type = find_sensor_type(type)
        records = self._find_sel_records_by_sensor_type(type)
        if len(records) != 0:
            raise AssertionError('SEL contains sensor type %s' % type)

    def wait_until_sel_contains_x_times_sensor_type(self, count, type):
        """Waits until the specified sensor type appears at least `count`
        times within the SEL.

        Note: this keyword invalidates the prefetched SEL records. You have to
        rerun the `Prefetch SEL` keyword.
        """

        type, type_name = find_sensor_type(type), type
        count = int(count)

        self._invalidate_prefetched_sel_records()
        start_time = time.time()
        while time.time() < start_time + self._timeout:
            records = self._find_sel_records_by_sensor_type(type)
            if len(records) >= count:
                self._selected_sel_record = records[0]
                return
            time.sleep(self._poll_interval)

        raise AssertionError('No match found for SEL record type "%s (%s)" in %s.'
                % (type_name, type, utils.secs_to_timestr(self._timeout)))


    def wait_until_sel_contains_x_times_sensor_number(self, count, number):
        """Waits until the specified sensor number appears at least `count`
        times within the SEL.

        Note: this keyword invalidates the prefetched SEL records. You have to
        rerun the `Prefetch SEL` keyword.
        """
        number = find_sensor_type(number)
        count = int(count)

        self._invalidate_prefetched_sel_records()
        start_time = time.time()
        while time.time() < start_time + self._timeout:
            records = self._find_sel_records_by_sensor_number(number)
            if len(records) >= count:
                self._selected_sel_record = records[0]
                return
            time.sleep(self._poll_interval)

        raise AssertionError('No match found for SEL record from num  "%d" in %s.'
                % (number, utils.secs_to_timestr(self._timeout)))

    def wait_until_sel_contains_sensor_type(self, type):
        """Wait until the SEL contains at least one record with the given
        sensor type.

        `type` is either an human readable string or the corresponding number.

        The SEL is polled with an interval, which can be set by `Set Poll
        Interval` or by `library loading`.

        The first matching entry is automatically selected, see `Select SEL
        Record By Sensor Type`.

        Note: this keyword invalidates the prefetched SEL records. You have to
        rerun the `Prefetch SEL` keyword.

        Example:
        | Set Timeout | 5 seconds |
        | Wait Until SEL Contains Sensor Type | 0x23 |
        | Wait Until SEL Contains Sensor Type | Voltage |
        """
        self.wait_until_sel_contains_x_times_sensor_type(1, type)

    def select_sel_record_at_offset(self, offset):
        """Selects a SEL record at offset.
        """
        offset = int_any_base(offset)
        self._selected_sel_record = self._sel_records[offset]

    def select_sel_record_by_sensor_type(self, type, index=1):
        """Selects a SEL record.

        Selected SEL records can be further examined by the `Selected SEL
        Records X`.

        `type` can be either a string or a number. See `Wait Until SEL Contains
        Sensor Type` for an example.

        If more than one entry match `index` can be used to select the
        subsequent ones. `index` can also be negative, see Python Sequences for
        more details on this.

        Example:
        | # Selects the first matching SEL entry |
        | Select SEL Record By Sensor Type | 0xcf |
        | # Selects the third matching SEL entry |
        | Select SEL Record By Sensor Type | 0xcf | 3 |
        | # Selects the last matching SEL entry |
        | Select SEL Record By Sensor Type | 0xcf | -1 |

        SENSOR_TYPE_TEMPERATURE = 0x01
        VOLTAGE = 0x02
        CURRENT = 0x03
        FAN = 0x04
        CHASSIS_INTRUSION = 0x05
        PLATFORM_SECURITY = 0x06
        PROCESSOR = 0x07
        POWER_SUPPLY = 0x08
        POWER_UNIT = 0x09
        COOLING_DEVICE = 0x0a
        OTHER_UNITS_BASED_SENSOR = 0x0b
        MEMORY = 0x0c
        DRIVE_SLOT = 0x0d
        POST_MEMORY_RESIZE = 0x0e
        SYSTEM_FIRMWARE_PROGRESS = 0x0f
        EVENT_LOGGING_DISABLED = 0x10
        WATCHDOG_1 = 0x11
        SYSTEM_EVENT = 0x12
        CRITICAL_INTERRUPT = 0x13
        BUTTON = 0x14
        MODULE_BOARD = 0x15
        MICROCONTROLLER_COPROCESSOR = 0x16
        ADD_IN_CARD = 0x17
        CHASSIS = 0x18
        CHIP_SET = 0x19
        OTHER_FRU = 0x1a
        CABLE_INTERCONNECT = 0x1b
        TERMINATOR = 0x1c
        SYSTEM_BOOT_INITIATED = 0x1d
        BOOT_ERROR = 0x1e
        OS_BOOT = 0x1f
        OS_CRITICAL_STOP = 0x20
        SLOT_CONNECTOR = 0x21
        SYSTEM_ACPI_POWER_STATE = 0x22
        WATCHDOG_2 = 0x23
        PLATFORM_ALERT = 0x24
        ENTITY_PRESENT = 0x25
        MONITOR_ASIC_IC = 0x26
        LAN = 0x27
        MANGEMENT_SUBSYSTEM_HEALTH = 0x28
        BATTERY = 0x29
        SESSION_AUDIT = 0x2a
        VERSION_CHANGE = 0x2b
        FRU_STATE = 0x2c
        FRU_HOT_SWAP = 0xf0
        IPMB_PHYSICAL_LINK = 0xf1
        MODULE_HOT_SWAP = 0xf2
        POWER_CHANNEL_NOTIFICATION = 0xf3
        TELCO_ALARM_INPUT = 0xf4
        """

        type = find_sensor_type(type)
        index = int(index)

        if index == 0:
            raise RuntimeError('index must not be zero')

        records = self._find_sel_records_by_sensor_type(type)
        if len(records) == 0:
            raise AssertionError(
                    'No SEL record found with sensor type "%s"' % type)
        try:
            if index > 0:
                index -= 1
            self._selected_sel_record = records[index]
        except IndexError:
            raise AssertionError(
                    'Only %d SEL records found with sensor type "%s"' %
                    (len(records), type))

    def select_sel_record_by_sensor_number(self, number, index=1):
        number = int_any_base(number)
        index = int(index)

        if index == 0:
            raise RuntimeError('index must not be zero')

        records = self._find_sel_records_by_sensor_number(number)
        if len(records) == 0:
            raise AssertionError(
                    'No SEL record found from sensor number "%d"' % number)
        try:
            if index > 0:
                index -= 1
            self._selected_sel_record = records[index]
        except IndexError:
            raise AssertionError(
                    'Only %d SEL records found from sensor number "%d"' %
                    (len(records), number))

    def select_sel_record_by_record_id(self, record_id):
        record_id = int_any_base(record_id)

        for record in self._sel_records:
            if record.record_id == record_id:
                self._selected_sel_record = record
                return

    def selected_sel_records_event_data_should_be_equal(self, expected_value,
            mask=0xffffff, msg=None):
        """Fails if the event data of the selected SEL record does not match
        the given value.

        Example:
        | Select SEL Record By Sensor Type | 0xcf |
        | Selected SEL Records Event Data Should Be Equal | 0xa10101 |
        | Selected SEL Records Event Data Should Be Equal | 0x010000 | 0x0f0000 |
        """

        expected_value = int_any_base(expected_value)
        mask = int_any_base(mask)

        record = self._selected_sel_record

        # apply mask
        expected_value = expected_value & mask
        actual_value = (record.event_data[0] << 16
                       | record.event_data[1] << 8
                       | record.event_data[2])
        actual_value = actual_value & mask
        expected_value = '0x%x' % expected_value
        actual_value = '0x%x' % actual_value
        asserts.assert_equal(expected_value, actual_value, msg)

    def selected_sel_records_event_direction_should_be(self,
            expected_direction, msg=None):
        """Fails if the direction of the selected SEL record does not mathc
        the given direction.

        `expected_direction` can be: Assertion, Deassertion
        """
        expected_direction = find_event_direction(expected_direction)
        actual_direction = self._selected_sel_record.event_direction

        asserts.assert_equal(expected_direction, actual_direction, msg)

    def selected_sel_record_should_be_from_sensor_number(self, expected_number,
             msg=None):
        """Fails if the sensor number of the selected SEL record does not match
        the given sensor number.
        """

        expected_number = int_any_base(expected_number)
        actual_number = self._selected_sel_record.sensor_number

        asserts.assert_equal(expected_number, actual_number, msg)

    def selected_sel_record_should_be_from_sensor_type(self, expected_type, msg=None):
        """Fails if the sensor type of the selected SEL record does not match
        the given sensor type.
        """

        expected_type = find_sensor_type(expected_type)
        actual_type = self._selected_sel_record.sensor_type

        asserts.assert_equal(expected_type, actual_type, msg)

    def get_sensor_number_from_selected_sel_record(self):
        """Returns the sensor number of the selected SEL record.
        """
        return self._selected_sel_record.sensor_number

    def get_selected_sel_entry_instance(self):
        """Returns the selected SEL entry instance
        """
        return self._selected_sel_record

    def set_event_receiver(self, ipmb_i2c_addr, lun=0):
        """
        """
        ipmb_i2c_addr = int_any_base(ipmb_i2c_addr)
        lun = int_any_base(lun)
        self._ipmi.set_event_receiver(ipmb_i2c_addr, lun)

    def get_event_receiver(self):
        """
        """
        return self._ipmi.get_event_receiver()
