#
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
#

import struct

EVENT_ASSERTION = 0
EVENT_DEASSERTION = 1

SENSOR_TYPE_TEMPERATURE                 = 0x01
SENSOR_TYPE_VOLTAGE                     = 0x02
SENSOR_TYPE_CURRENT                     = 0x03
SENSOR_TYPE_FAN                         = 0x04
SENSOR_TYPE_CHASSIS_INTRUSION           = 0x05
SENSOR_TYPE_PLATFORM_SECURITY           = 0x06
SENSOR_TYPE_PROCESSOR                   = 0x07
SENSOR_TYPE_POWER_SUPPLY                = 0x08
SENSOR_TYPE_POWER_UNIT                  = 0x09
SENSOR_TYPE_COOLING_DEVICE              = 0x0A
SENSOR_TYPE_OTHER_UNITS_BASED_SENSOR    = 0x0B
SENSOR_TYPE_MEMORY                      = 0x0C
SENSOR_TYPE_DRIVE_SLOT                  = 0x0D
SENSOR_TYPE_POST_MEMORY_RESIZE          = 0x0E
SENSOR_TYPE_SYSTEM_FIRMWARE_PROGRESS    = 0x0F
SENSOR_TYPE_EVENT_LOGGING_DISABLED      = 0x10
SENSOR_TYPE_WATCHDOG_1                  = 0x11
SENSOR_TYPE_SYSTEM_EVENT                = 0x12
SENSOR_TYPE_CRITICAL_INTERRUPT          = 0x13
SENSOR_TYPE_BUTTON                      = 0x14
SENSOR_TYPE_MODULE_BOARD                = 0x15
SENSOR_TYPE_MICROCONTROLLER_COPROCESSOR = 0x16
SENSOR_TYPE_ADD_IN_CARD                 = 0x17
SENSOR_TYPE_CHASSIS                     = 0x18
SENSOR_TYPE_CHIP_SET                    = 0x19
SENSOR_TYPE_OTHER_FRU                   = 0x1A
SENSOR_TYPE_CABLE_INTERCONNECT          = 0x1B
SENSOR_TYPE_TERMINATOR                  = 0x1C
SENSOR_TYPE_SYSTEM_BOOT_INITIATED       = 0x1D
SENSOR_TYPE_BOOT_ERROR                  = 0x1E
SENSOR_TYPE_OS_BOOT                     = 0x1F
SENSOR_TYPE_OS_CRITICAL_STOP            = 0x20
SENSOR_TYPE_SLOT_CONNECTOR              = 0x21
SENSOR_TYPE_SYSTEM_ACPI_POWER_STATE     = 0x22
SENSOR_TYPE_WATCHDOG_2                  = 0x23
SENSOR_TYPE_PLATFORM_ALERT              = 0x24
SENSOR_TYPE_ENTITY_PRESENT              = 0x25
SENSOR_TYPE_MONITOR_ASIC_IC             = 0x26
SENSOR_TYPE_LAN                         = 0x27
SENSOR_TYPE_MANGEMENT_SUBSYSTEM_HEALTH  = 0x28
SENSOR_TYPE_BATTERY                     = 0x29
SENSOR_TYPE_SESSION_AUDIT               = 0x2A
SENSOR_TYPE_VERSION_CHANGE              = 0x2B
SENSOR_TYPE_FRU_STATE                   = 0x2C
SENSOR_TYPE_FRU_HOT_SWAP                = 0xF0
SENSOR_TYPE_IPMB_PHYSICAL_LINK          = 0xF1
SENSOR_TYPE_MODULE_HOT_SWAP             = 0xF2
SENSOR_TYPE_POWER_CHANNEL_NOTIFICATION  = 0xF3
SENSOR_TYPE_TELCO_ALARM_INPUT           = 0xF4


class NotSupportedError(Exception):
    pass

class Sel:
    def __init__(self):
        pass

    def fetch_sel(self):
        """Fetches the sensor event log.

        Fetching the SEL is required for all further operation on the SEL.

        See `Sel Should Contain X Times Sensor Type`, `Select Sel Record By
        Sensor Type` and `Wait Until Sel Contains Sensor Type`.
        """

        del self._cp['sel_records'][:]
        self._cp['sel_records'] = self._ipmi.get_sel_entries()
        for r in self._cp['sel_records']:
            self._info('SEL dump:\n%s' % r)

    def clear_sel(self):
        """Clears the sensor event log."""

        self._ipmi.clear_sel()

    def log_sel(self):
        """Dumps the sensor event log and logs it."""

        records = self._ipmi.get_sel_entries()
        for r in records:
            self._info('SEL dump:\n%s' % r)

    def _find_sel_records_by_sensor_type(self, type):
        matches = []
        for record in self._cp['sel_records']:
            if record.sensor_type == type:
                matches.append(record)
        return matches

    def _find_sel_records_by_sensor_number(self, number):
        matches = []
        for record in self._cp['sel_records']:
            if record.sensor_number == number:
                matches.append(record)
        return matches

    def sel_should_contain_x_entries(self, count, msg=None):
        """Fails if the SEL does not contain `count` entries.
        """
        count = int(count)
        asserts.fail_unless_equal(count, len(self._cp['sel_records']), msg)

    def sel_should_contain_x_times_sensor_type(self, type, count, msg=None):
        """Fails if the SEL does not contain `count` times an event with the
        given sensor type.
        """

        type = find_sensor_type(type)
        count = int(count)

        records = self._find_sel_records_by_sensor_type(type)
        asserts.fail_unless_equal(count, len(records), msg)

    def sel_should_not_contain_sensor_type(self, type, msg=None):
        """Fails if SEL contains the given sensor type.
        """

        type = find_sensor_type(type)
        records = self._find_sel_records_by_sensor_type(type)
        if len(records) != 0:
            raise AssertionError('SEL contains sensor type %s' % type)

    def wait_until_sel_contains_x_times_sensor_type(self, count, type):
        type = find_sensor_type(type)
        count = int(count)

        start_time = time.time()
        while time.time() < start_time + self._timeout:
            self.fetch_sel()
            records = self._find_sel_records_by_sensor_type(type)
            if len(records) >= count:
                self._cp['selected_sel_record'] = records[0]
                return
            time.sleep(self._poll_interval)

        raise AssertionError('No match found for SEL record type "%s" in %s.'
                % (type, utils.secs_to_timestr(self._timeout)))


    def wait_until_sel_contains_x_times_sensor_number(self, count, number):
        number = find_sensor_type(number)
        count = int(count)

        start_time = time.time()
        while time.time() < start_time + self._timeout:
            self.fetch_sel()
            records = self._find_sel_records_by_sensor_number(number)
            if len(records) >= count:
                self._cp['selected_sel_record'] = records[0]
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

        Example:
        | Set Timeout | 5 seconds |
        | Wait Until SEL Contains Sensor Type | 0x23 |
        | Wait Until SEL Contains Sensor Type | Voltage |
        """
        self.wait_until_sel_contains_x_times_sensor_type(1, type)

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
            self._cp['selected_sel_record'] = records[index]
        except IndexError:
            raise AssertionError(
                    'Only %d SEL records found with sensor type "%s"' %
                    (len(records), type))

    def select_sel_record_by_sensor_number(self, number, index=1):
        number = find_sensor_type(number)
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
            self._cp['selected_sel_record'] = records[index]
        except IndexError:
            raise AssertionError(
                    'Only %d SEL records found from sensor number "%d"' %
                    (len(records), number))

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

        if 'selected_sel_record' not in self._cp:
            raise RuntimeError('No SEL record selected.')

        record = self._cp['selected_sel_record']

        # apply mask
        expected_value = expected_value & mask
        actual_value = (ord(record.event_data[0]) << 16
                | ord(record.event_data[1]) << 8
                | ord(record.event_data[2]))
        actual_value = actual_value & mask

        asserts.fail_unless_equal(expected_value, actual_value, msg)

    def selected_sel_records_event_direction_should_be(self,
            expected_direction, msg=None):
        expected_direction = find_event_direction(expected_direction)
        actual_direction = self._cp['selected_sel_record'].event_direction

        asserts.fail_unless_equal(expected_direction, actual_direction, msg)

    def selected_sel_record_should_be_from_sensor_number(self, sensor_number,
             msg=None):
        """
        """
        sensor_number = int_any_base(sensor_number)

        if not self._selected_sel_record:
            raise RuntimeError('No SEL record selected.')
        asserts.fail_unless_equal(sensor_number,
                self._selected_sel_record.sensor_number, msg)

class SelRecord:
    def decode_hex(self, hexdata):
        self._parse_sel_record(hexdata.decode('hex'))

    def decode_binary(self, data):
        self._parse_sel_record(data)

    def __str__(self):
        str = []
        str.append('SEL Record ID %d' % self.id)
        str.append('  Type %d' % self.type)
        str.append('  Timestamp %d' % self.timestamp)
        if 'i2c_slave_address' in dir(self):
            str.append('  I2C Slave Address 0x%02x' % self.i2s_slave_address)
        if 'system_software_id' in dir(self):
            str.append('  System Software ID 0x%02x' % self.system_software_id)
        str.append('  Channel Number %d' % self.channel_number)
        str.append('  IPMB device lun %d' % self.ipmb_device_lun)
        str.append('  EvM rev %d' % self.evm_rev)
        str.append('  Sensor Type %d' % self.sensor_type)
        str.append('  Sensor Number %d' % self.sensor_number)
        str.append('  Event Direction %d' % self.event_direction)
        str.append('  Event Type %d' % self.event_type)
        str.append('  Event Data 0x%06x' % self.event_data)
        return "\n".join(str)

    def _parse_sel_record(self, data):
        data = struct.unpack('<HBIBBBBBBBBB', data)
        record = {}
        self.id = data[0]
        self.type = data[1]
        if self.type != 0x02:
            raise NotSupportedError('Only system events are supported.')

        self.timestamp = data[2]
        if data[3] & 0x01:
            self.i2c_slave_address = (data[3] >> 1) & 0x3f
        else:
            self.system_software_id = (data[3] >> 1) & 0x3f
        self.channel_number = (data[4] >> 4) & 0x0f
        self.ipmb_device_lun = data[4] & 0x03
        self.evm_rev = data[5]
        if self.evm_rev != 0x04:
            raise NotSupportedError('Only v1.5 events are supported.')
        self.sensor_type = data[6]
        self.sensor_number = data[7]
        self.event_direction = (data[8] >> 7) & 0x1
        self.event_type = data[8]
        self.event_data = data[9] << 16 | data[10] << 8 | data[11]

