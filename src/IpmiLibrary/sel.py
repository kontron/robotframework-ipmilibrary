# 
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
#

import struct

class NotSupportedException:
    pass

class SelRecord:
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
            raise NotSupportedException('Only system events are supported.')

        self.timestamp = data[2]
        if data[3] & 0x01:
            self.i2c_slave_address = (data[3] >> 1) & 0x3f
        else:
            self.system_software_id = (data[3] >> 1) & 0x3f
        self.channel_number = (data[4] >> 4) & 0x0f
        self.ipmb_device_lun = data[4] & 0x03
        self.evm_rev = data[5]
        if self.evm_rev != 0x04:
            raise NotSupportedException('Only v1.5 events are supported.')
        self.sensor_type = data[6]
        self.sensor_number = data[7]
        self.event_direction = (data[8] >> 7) & 0x1
        self.event_type = data[8]
        self.event_data = data[9] << 16 | data[10] << 8 | data[11]

