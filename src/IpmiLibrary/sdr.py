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

import time
import array

from robot import utils
from robot.utils import asserts
from robot.utils.connectioncache import ConnectionCache
from robot.output import LOGGER
from robot.output.loggerhelper import Message

from .utils import int_any_base
from .mapping import *


class Sdr:

    def set_sdr_source(self, source):
        """Select the SDR source. This specifies if the keywords that fetch and
        check SDRs collect the SDR data from the sensor device or form the SDR
        repository device.

        Example:
        | Set SDR Source | Sensor Device  |
        | Set SDR Source | SDR Repository |
        """
        if source.lower() in ('sensor device', 'sdr repository'):
            self._cp['sdr_source'] = source.lower()

    def _get_sdr_list(self):
        if self._cp['sdr_source'] == 'sensor device':
            return self._ipmi.get_device_sdr_list()
        elif self._cp['sdr_source'] == 'sdr repository':
            return self._ipmi.get_repository_sdr_list()
        else:
            raise RuntimeError

    def _sdr_entries(self):
        if self._cp['sdr_source'] == 'sensor device':
            return self._ipmi.device_sdr_entries()
        elif self._cp['sdr_source'] == 'sdr repository':
            return self._ipmi.sdr_repository_entries()
        else:
            raise RuntimeError


    def get_sdr_repository_info(self):
        """Returns the SDR Repository Info.
        """
        return self._ipmi.get_sdr_repository_info()

    def get_sdr_repository_allocation_info(self):
        """Returns the SDR Repository Allocation Info.
        """
        return self._ipmi.get_sdr_repository_allocation_info()

    def reserve_sdr_repository(self):
        """Returns the SDR Repository Reservation Id.
        """
        return self._ipmi.reserve_sdr_repository()

    def clear_sdr_repository(self):
        """Clear the SDR repository and wait until erasure is finished.
        """
        return self._ipmi.clear_sdr_repository()

    def delete_sdr(self, record_id):
        """Delete the SDR from repository specified by 'record_id'.
        """
        record_id = int_any_base(record_id)
        return self._ipmi.delete_sdr(record_id)

    def run_initialization_agent(self):
        self._ipmi.start_initialization_agent()

    def get_initialization_agent_status(self):
        return self._ipmi.get_initialization_agent_status()

    def partial_add_sdr(self, reservation_id,
            record_id, offset, progress, data):
        record_id = int_any_base(record_id)
        offset = int_any_base(offset)
        progress = int_any_base(progress)

        if isinstance(data, basestring):
            data = [int_any_base(d) for d in data.split(' ')]
        elif isinstance(data, list):
            data = data
        else:
            data = [int_any_base(data)]
        data = array.array('c', [chr(c) for c in data])

        return self._ipmi.partial_add_sdr(
                reservation_id, record_id, offset, progress, data)

    @property
    def _sdr_list(self):
        if 'prefetched_sdr_list' in self._cp:
            return self._cp['prefetched_sdr_list']
        else:
            return self._get_sdr_list()

    @property
    def _selected_sdr(self):
        try:
            return self._cp['selected_sdr']
        except KeyError:
            AssertionError('No SDR selected.')

    _selected_sdr.setter
    def _selected_sdr(self, value):
        self._cp['selected_sdr'] = value

    def prefetch_sdr_list(self):
        if 'prefetched_sdr_list' in self._cp:
            del self._cp['prefetched_sdr_list']
        self._cp['prefetched_sdr_list'] = self._sdr_list
        self._info('Prefetching SDR list')

    def log_sdr_list(self):
        print('*INFO* SDR list')
        for sdr in self._sdr_list:
            print(sdr)

    def _find_sdr_by_name(self, name):
        for sdr in self._sdr_list:
            if sdr.device_id_string == name:
                return sdr

        raise AssertionError('SDR with name "%s" not found in list' % (name))

    def _find_sdr_by_record_id(self, sdr_id):
        for sdr in self._sdr_list:
            if sdr.id == sdr_id:
                return sdr

        raise AssertionError('SDR with ID "%x" not found' % sdr_id)

    def _find_sdr_by_record_type(self, record_type):
        for sdr in self._sdr_list:
            if sdr.type == record_type:
                return sdr

    def _find_sdr_by_sensor_type(self, sensor_type):
        for sdr in self._sdr_list:
            if hasattr(sdr, 'sensor_type_code'):
                if sdr.sensor_type_code == sensor_type:
                    return sdr

    def select_sdr_by_record_id(self, record_id):
        """Selects a SDR by its record id.
        """
        record_id = int_any_base(record_id)
        self._selected_sdr = self._find_sdr_by_record_id(record_id)

    def select_sdr_by_name(self, name):
        """Selects a SDR by its name.
        """
        self._selected_sdr = self._find_sdr_by_name(name)

    def select_sdr_by_record_type(self, record_type):
        """Selects SDR by its record type.

        `record_type`
        """

        record_type = find_sdr_record_type(record_type)
        self._selected_sdr = self._find_sdr_by_record_type(record_type)

    def select_sdr_by_sensor_type(self, sensor_type):
        """Selects SDR by its sensor type.

        `sensor_type`
        """
        sensor_type = find_sdr_sensor_type(sensor_type)
        self._selected_sdr = self._find_sdr_by_sensor_type(sensor_type)

    def selected_sdr_name_should_be_equal(self, expected_name, msg=None):
        """Fails unless the name of the selected sensor matches the given one.
        """

        actual_name = self._selected_sdr.device_id_string
        asserts.assert_equal(expected_name, actual_name, msg)

    def selected_sdr_sensor_state_should_be_equal(self, expected_state,
                mask=0x7fff, msg=None):
        """Fails unless the state of the selected senor matches the given
        one.
        """

        expected_state = int_any_base(expected_state)
        mask = int_any_base(mask)

        self.sensor_state_should_be_equal(self._selected_sdr.device_id_string,
                expected_state, self._selected_sdr, mask, msg)

    def selected_sdr_sensor_reading_should_be_equal(self, expected_reading,
                msg=None):
        """Fails unless the reading of the selected sensor matches the given
        one.

        Note: `expected_reading` is the converted value, not the raw reading.
        """

        expected_reading = float(expected_reading)

        self.sensor_reading_should_be_equal(self._selected_sdr,
                expected_reading, msg)

    def selected_sdr_entity_id_should_be(self, expected_entity_id, msg=None):
        """Fails unless the entity ID of the selected SDR matches the given
        one.

        Possible `entity_id`s are: Power Module, Cooling Unit, PICMG Front
        Board, PICMG Rear Transition Module, PICMG Advanced MC, PICMG Microtca
        Carrier Hub, PICMG Shelf Management Controller, PICMG Filtration Unit,
        PICMG Shelf Fru Information
        """

        expected_entity_id = find_entity_type_id(expected_entity_id)
        actual_entity_id = self._selected_sdr.entity_id

        asserts.assert_equal(expected_entity_id, actual_entity_id, msg)

    def selected_sdr_entity_instance_should_be(self, expected_entity_instance,
             msg=None):
        expected_entity_instance = int_any_base(expected_entity_instance)
        actual_entity_instance = self._selected_sdr.entity_instance

        asserts.assert_equal(expected_entity_instance,
            actual_entity_instance, msg)

    def selected_sdr_type_should_be(self, expected_sdr_type, msg=None):
        """Fails unless the SDR type of the selected SDR matches the given
        one.

        Possible `sdr_type`s are: Full Sensor Record, Compact Sensor Record,
        Entity Association Record, Fru Device Locator Record, Management
        Controller Device Locator Record, Management Controller Confirmation
        Record, BMC Message Channel Info Record
        """

        expected_sdr_type = find_sdr_record_type(expected_sdr_type)
        actual_sdr_type = self._selected_sdr.type

        asserts.assert_equal(expected_sdr_type, actual_sdr_type)

    def get_sensor_number_for_sensor_name(self, name, sdr=None):
        """Return the sensor number that is specified by name.
        """
        self.select_sdr_by_name(name)

        if sdr is None:
            sdr = self._find_sdr_by_name(name)

        return sdr.number


    def sensor_state_should_be_equal(self, name, expected_state, sdr=None,
            mask=0x7fff, msg=None):
        """Fails unless the sensor state of the sensor with name `name` matches
        the given one.
        """

        expected_state = int_any_base(expected_state)
        mask = int_any_base(mask)

        if sdr is None:
            sdr = self._find_sdr_by_name(name)
        (_, actual_state) = self._ipmi.get_sensor_reading(sdr.number)

        # apply mask
        expected_state = expected_state & mask
        actual_state = actual_state & mask

        asserts.assert_equal(expected_state, actual_state, msg)

    def sensor_reading_should_be_equal(self, name, expected_reading, msg=None):
        """Fails unless the sensor reading of the sensor with name `name`
        matches the given one.
        """

        expected_reading = float(expected_reading)

        sdr = self._find_sdr_by_name(name)
        (raw, _) = ac._ipmi.get_sensor_reading(sdr.number)
        if raw is not None:
            actual_reading = sdr.convert_sensor_reading(raw)
        else:
            actual_reading = None
        asserts.assert_equal(expected_value, actual_reading, msg)

    def sdr_should_be_present(self, name):
        """Fails unless the SDR with the given name is present.
        """
        try:
            self._find_sdr_by_name(name)
        except:
            raise AssertionError('Sensor "%s" is not present' % name)

    def get_sdr_instance_by_record_id(self, record_id):
        """Returns the SDR object of the SDR with record id `record_id`.
        """
        return self._find_sdr_by_record_id(record_id)

    def get_sdr_instance(self, name):
        """Returns the SDR object of the SDR with name `name`.
        """
        return self._find_sdr_by_name(name)

    def get_sensor_number(self, name):
        """Returns the sensor number for the given SDR name.

        `name` is the sensor ID string given in the SDR.
        """
        sdr = self._find_sdr_by_name(name)
        if not sdr.number:
            raise RuntimeError('SDR "%s" has no sensor number' % name)

        return sdr.number

    def get_sensor_reading(self, name):
        """Returns a sensor reading.

        `name` is the sensor ID string given in the SDR.
        """

        sdr = self._find_sdr_by_name(name)
        (raw, _) = self._ipmi.get_sensor_reading(sdr.number)
        if raw is not None:
            reading = sdr.convert_sensor_raw_to_value(raw)
        else:
            reading = None

        return reading

    def get_sensor_state(self, name, sdr=None):
        """Returns the assertion state of a sensor.

        `name` is the sensor ID string. See also `Get Sensor Reading`.
        """

        if sdr is None:
            sdr = self._find_sdr_by_name(name)

        (_, states) = self._ipmi.get_sensor_reading(sdr.number)

        return states

    def _check_valid_threshold_name(self, threshold):
        if threshold not in ('lnr', 'lcr', 'lnc', 'unc', 'ucr', 'unr'):
            raise RuntimeError('Invalid threshold "%s"' % threshold)

    def get_sensor_threshold(self, name, threshold):
        """Returns the current threshold for a sensor.

        `name` is the sensor ID string. See also `Get Sensor Reading`.

        `threshold` can be one of the following strings: "lnr", "lcr", "lnc",
        "unc", "ucr", "unr".

        Example:
        | ${threshold}= | Get Sensor Threshold | Vcc +12V | lnr |
        """

        threshold = threshold.lower()
        self._check_valid_threshold_name(threshold)

        sdr = self._find_sdr_by_name(name)

        thresholds = self._ipmi.get_sensor_thresholds(sdr.number, sdr.owner_lun)

        converted_thresholds = {}
        for t in ('lnr', 'lcr', 'lnc', 'unc', 'ucr', 'unr'):
            if thresholds.has_key(t):
                converted_thresholds[t] \
                    = sdr.convert_sensor_raw_to_value(thresholds[t])
        return converted_thresholds[threshold]

    def set_sensor_threshold(self, name, threshold, value):
        """Sets the threshold of a sensor.

        For the `name` and `threshold` parameters see `Get Sensor Threshold`.
        """

        threshold = threshold.lower()
        value = float(value)
        self._check_valid_threshold_name(threshold)

        sdr = self._find_sdr_by_name(name)
        thresholds = {}
        thresholds[threshold] = sdr.convert_sensor_value_to_raw(value)
        self._ipmi.set_sensor_thresholds(sdr.number, sdr.owner_lun,
                **thresholds)

    def wait_until_sensor_state_is(self, name, state, mask=0x7fff):
        """Wait until a sensor reaches the given state.

        `name` is the sensor ID string. See also `Get Sensor Reading`.
        """

        state = int_any_base(state)
        mask = int_any_base(mask)

        start_time = time.time()
        while time.time() < start_time + self._timeout:
            current_state = self.get_sensor_state(name)
            if current_state & mask == state & mask:
                self._info('waited %s seconds until state "%s" was reached'
                        % (time.time()-start_time, state))
                return
            time.sleep(self._poll_interval)

        raise AssertionError('Sensor "%s" did not reach the state "%s" in %s.'
                % (name, state, utils.secs_to_timestr(self._timeout)))

    def wait_until_sensor_reading_is(self, name, value):
        """Wait until a sensor reaches the given value.

        `name` is the sensor ID string. See also `Get Sensor Reading`.
        """

        value = float(value)

        start_time = time.time()
        while time.time() < start_time + self._timeout:
            current_reading = self.get_sensor_reading(name)
            if current_reading == value:
                self._info('waited %s seconds until value "%s" was reached'
                        % (time.time()-start_time, value))
                return
            time.sleep(self._poll_interval)

        raise AssertionError('Sensor "%s" did not reach the value "%s" in %s.'
                % (name, value, utils.secs_to_timestr(self._timeout)))
