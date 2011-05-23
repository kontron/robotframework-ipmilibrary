#
# Kontron IpmiLibrary
#
# author: Heiko Thiery <heiko.thiery@kontron.com>
#

import time

from robot import utils
from robot.utils import asserts
from robot.utils.connectioncache import ConnectionCache
from robot.output import LOGGER
from robot.output.loggerhelper import Message

from utils import int_any_base
from mapping import *


class Sdr:
    def __init__(self):
        pass

    def log_sdr_list(self):
        ac = self._active_connection

        if len(ac._sdr_list) == 0:
            self.fetch_sdr_list()

        for sdr in ac._sdr_list:
            self._trace('%s' % sdr)

    def fetch_sdr_list(self):
        ac = self._active_connection
        del ac._sdr_list[:]
        self._trace('fetch SDR list')
        ac._sdr_list = ac._ipmi.get_sdr_list()
        for sdr in ac._sdr_list:
            self._trace('ID=%04x STRING=%s' % (sdr.id, sdr.device_id_string))

    def _find_sdr_by_name(self, name):
        name = str(name)
        ac = self._active_connection

        if len(ac._sdr_list) == 0:
            self.fetch_sdr_list()

        for sdr in ac._sdr_list:
            if sdr.device_id_string == name:
                return sdr

        for sdr in ac._sdr_list:
           self._trace('ID=%04x string=%s' % (sdr.id, sdr.device_id_string))
        raise AssertionError('SDR with name "%s" not found in list' % (name))

    def _find_sdr_by_record_id(self, sdr_id):
        sdr_id = int_any_base(sdr_id)
        ac = self._active_connection

        if len(ac._sdr_list) == 0:
            self.fetch_sdr_list()

        for sdr in ac._sdr_list:
            if sdr.id == sdr_id:
                return sdr
        raise AssertionError('SDR with ID "%x" not found' % sdr_id)

    def select_sdr_by_name(self, name):
        """
        """
        ac = self._active_connection
        ac._selected_sdr = self._find_sdr_by_name(name)

    def select_sdr_by_record_type(self, record_type):
        """Select SDR by record type.

        `record_type`
        """
        record_type = find_sdr_record_type(record_type)
        ac = self._active_connection

        for sdr in ac._sdr_list:
            if sdr.type == record_type:
                ac._selected_sdr = sdr
                return sdr

    def selected_sdr_name_should_be_equal(self, name, msg=None):
        """
        """
        name = str(name)
        ac = self._active_connection
        sdr = ac._selected_sdr
        if not sdr:
            AssertionError('no SDR selected')

        asserts.fail_unless_equal(name, sdr.device_id_string, msg)

    def selected_sdr_sensor_value_should_be_equal(self, expected_value,
                mask=0x7fff, msg=None):
        """
        """
        expected_value = int_any_base(expected_value)
        ac = self._active_connection

        sdr = ac._selected_sdr
        if not sdr:
            AssertionError('no SDR selected')

        self.sensor_value_should_be_equal(sdr.device_id_string,
                expected_value, mask, msg)

    def selected_sdr_sensor_reading_should_be(self, expected_reading, msg=None):
        """
        """
        expected_reading = str(expected_reading)
        ac = self._active_connection

        sdr = ac._selected_sdr
        if not sdr:
            AssertionError('no SDR selected')
        self.sensor_reading_should_be_equal(sdr.device_id_string,
                expected_reading, msg=None)

    def selected_sdr_entity_id_should_be(self, entity_id, msg=None):
        """
        `entity_id` possible ids are:

        Power Module
        Cooling Unit
        PICMG Front Board
        PICMG Rear Transition Module
        PICMG Advanced MC
        PICMG Microtca Carrier Hub
        PICMG Shelf Management Controller
        PICMG Filtration Unit
        PICMG Shelf Fru Information
        """
        ac = self._active_connection
        entity_id = find_entity_type_id(entity_id)
        asserts.fail_unless_equal(entity_id, ac._selected_sdr.entity_id)

    def selected_sdr_type_should_be(self, sdr_type, msg=None):
        """Fails if the selected SDR is not from specified type

        `sdr_type` possible types are:

        Full Sensor Record
        Compact Sensor Record
        Entity Association Record
        Fru Device Locator Record
        Management Controller Device Locator Record
        Management Controller Confirmation Record
        BMC Message Channel Info Record
        """
        ac = self._active_connection
        sdr_type = find_sdr_record_type(sdr_type)
        asserts.fail_unless_equal(sdr_type, ac._selected_sdr.type)

    def sensor_value_should_be_equal(self, name, expected_value,
            mask=0x7fff, msg=None):
        """
        """
        expected_value = int_any_base(expected_value)
        mask = int_any_base(mask)
        ac = self._active_connection

        sdr = self._find_sdr_by_name(name)
        (raw, states) = ac._ipmi.get_sensor_reading(sdr.number)
        # apply mask
        expected_value = expected_value & mask
        value = states & mask
        asserts.fail_unless_equal(expected_value, value, msg)

    def sensor_reading_should_be_equal(self, name, expected_reading, msg=None):
        """
        """
        expected_reading = str(expected_reading)
        ac = self._active_connection

        sdr = self._find_sdr_by_name(name)
        (raw, states) = ac._ipmi.get_sensor_reading(sdr.number)
        reading = sdr.convert_sensor_reading(raw)
        # apply mask
        asserts.fail_unless_equal(expected_value, value, msg)

    def sdr_should_be_present(self, name):
        """Fails if the SDR with the given name is not present.
        """
        sdr = self._find_sdr_by_name(name)
        if not sdr:
            raise RuntimeError('No sensor found with name "$s"' % name)

    def get_sdr_instance(self, name):
        """Returns the SDR object instance of the SDR.
        """
        name = str(name)
        sdr = self._find_sdr_by_name(name)
        return sdr

    def get_sensor_number(self, name):
        """Returns the sensor number for the given SDR name.

        `name` is the sensor ID string given in the SDR
        """
        name = str(name)
        ac = self._active_connection

        sdr = self._find_sdr_by_name(name)
        if sdr.number:
            sensor_number = sdr.number
            return sensor_number
        else:
            raise RuntimeError('SDR "%s" has no sensor number' % name)

    def get_sensor_reading(self, name):
        """Returns a sensor reading.

        `name` is the sensor ID string given in the SDR
        """
        name = str(name)
        ac = self._active_connection

        sdr = self._find_sdr_by_name(name)
        (raw, states) = ac._ipmi.get_sensor_reading(sdr.number)
        return sdr.convert_sensor_reading(raw)

    def get_sensor_state(self, name):
        """Returns the assertion state of a sensor.

        `name` is the sensor ID string. See also `Get Sensor Reading`.
        """
        name = str(name)
        ac = self._active_connection

        sdr = self._find_sdr_by_name(name)
        self._trace("%s, %d" % (sdr.device_id_string, sdr.number))
        (raw, states) = ac._ipmi.get_sensor_reading(sdr.number)
        return states

    def get_sensor_threshold(self, name, threshold):
        """Returns the current threshold for a sensor.

        `name` is the sensor ID string. See also `Get Sensor Reading`.

        `threshold` can be one of the following strings: "lnr", "lcr", "lnc",
        "unc", "ucr", "unr".

        Example:
        | ${threshold}= | Get Sensor Threshold | Vcc +12V | lnr |

        """
        name = str(name)
        treshold = str(threshold).lower()

        sdr = self._find_sdr_by_name(name)
        if not sdr:
            raise AssertionError('SDR with name "%s" no found' % name)

        thresholds = {}
        thresholds['unr'] = sdr.convert_sensor_reading(sdr.threshold_unr)
        thresholds['ucr'] = sdr.convert_sensor_reading(sdr.threshold_ucr)
        thresholds['unc'] = sdr.convert_sensor_reading(sdr.threshold_unc)
        thresholds['lnc'] = sdr.convert_sensor_reading(sdr.threshold_lnc)
        thresholds['lcr'] = sdr.convert_sensor_reading(sdr.threshold_lcr)
        thresholds['lnr'] = sdr.convert_sensor_reading(sdr.threshold_lnr)

        try:
            return thresholds[threshold]
        except KeyError:
            raise RuntimeError('Threshold "%s" not found for sensor "%s"' %
                    (threshold, name))

    def wait_until_sensor_state_is(self, name, state, mask=0x7fff):
        """Wait until a sensor reaches the given state.

        `name` is the sensor ID string. See also `Get Sensor Reading`.
        """
        name = str(name)
        state = int_any_base(state)
        ac = self._active_connection

        start_time = time.time()
        while time.time() < start_time + ac._timeout:
            current_state = self.get_sensor_state(name)
            if current_state & mask == state & mask:
                self._trace('waited %s seconds until state "%s" was reached'
                        % (time.time()-start_time, state))
                return
            time.sleep(ac._poll_interval)

        raise AssertionError('Sensor "%s" did not reach the state "%s" in %s.'
                % (name, state, utils.secs_to_timestr(ac._timeout)))

    def wait_until_sensor_value_is(self, name, value):
        """Wait until a sensor reaches the given value.

        `name` is the sensor ID string. See also `Get Sensor Reading`.
        """
        name = str(name)
        value = int_any_base(value)
        ac = self._active_connection

        start_time = time.time()
        while time.time() < start_time + ac._timeout:
            current_value = self.get_sensor_reading(name)
            if current_value == value:
                self._trace('waited %s seconds until value "%s" was reached'
                        % (time.time()-start_time, value))
                return
            time.sleep(ac._poll_interval)

        raise AssertionError('Sensor "%s" did not reach the value "%s" in %s.'
                % (name, state, utils.secs_to_timestr(ac._timeout)))
