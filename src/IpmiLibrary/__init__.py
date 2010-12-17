# 
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
#

import time
from sel import SelRecord
from subprocess import Popen, PIPE
from robot import utils
from robot.utils import asserts
from utils import find_attribute, int_any_base
from robot.utils.connectioncache import ConnectionCache

class IpmiConnection:
    def __init__(self, host, target_address, user, password,
            bridge_channel, double_bridge_target_address):
        self.host = host
        self.target_address = target_address
        self.user = user
        self.password = password
        self.bridge_channel = bridge_channel;
        self.double_bridge_target_address = double_bridge_target_address

    def close(self):
        # connectioncache calls this function
        pass

class IpmiLibrary:
    IPMITOOL = 'ipmitool'

    def __init__(self, timeout=3.0, poll_interval=1.0):
        self._sel_records = []
        self._selected_sel_record = None
        self.set_timeout(timeout)
        self.set_poll_interval(timeout)
        self._cache = ConnectionCache()

    def open_ipmi_connection(self, host, target_address, user='', password='',
            bridge_channel=None, double_bridge_target_address=None, alias=None):
        """Opens a LAN connection to an IPMI shelf manager.
 
        `host` is the IP or hostname of the shelf manager. `target_address` the
        IPMI address to which the command should be sent. `user` and `password`
        are used to authenticate against the shelf manager.
        """

        host = str(host)
        target_address = int_any_base(target_address)
        user = str(user)
        password = str(password)

        if bridge_channel:
            bridge_channel = int_any_base(bridge_channel)
        if double_bridge_target_address:
            double_bridge_target_address = int_any_base(double_bridge_target_address)
        if alias:
            alias = str(alias)

        self._info('Opening IPMI connection to %s:0x%02x' % (host,
            target_address))

        conn = IpmiConnection(host, target_address, user, password,
                bridge_channel, double_bridge_target_address)
        self._active_connection = conn

        return self._cache.register(conn, alias)

    def switch_ipmi_connection(self, index_or_alias):
        """Switches between active connections using an index or alias.

        The index is got from `Open IPMI Connection` keyword, and an alias can
        be given to it.

        Returns the index of previously active conection.
        """

        old_index = self._cache.current_index
        self._active_connection = self._cache.switch(index_or_alias)
        return old_index

    def close_all_ipmi_connections(self):
        """Closes all open connections and empties the connection cache.

        After this keyword, new indexes got from the `Open Connection`
        keyword are reset to 1.

        This keyword should be used in a test or suite teardown to
        make sure all connections are closed.
        """
        self._active_connection = self._cache.close_all()

    def close_ipmi_connection(self, loglevel=None):
        """Closes the current connection.
        """
        self._active_connection.close()

    def _run_ipmitool(self, ipmi_cmd):
        cmd = self.IPMITOOL
        cmd += (' -I lan')
        cmd += (' -H %s' % self._active_connection.host)

        if self._active_connection.bridge_channel:
            cmd += (' -b %d' % self._active_connection.bridge_channel)

        if self._active_connection.double_bridge_target_address:
            cmd += (' -t 0x%02x' %
                    self._active_connection.double_bridge_target_address)
            cmd += (' -T 0x%02x' % self._active_connection.target_address)
        else:
            cmd += (' -t 0x%02x' % self._active_connection.target_address)

        cmd += (' -U "%s"' % self._active_connection.user)
        cmd += (' -P "%s"' % self._active_connection.password)
        cmd += (' %s 2>&1' % ipmi_cmd)

        self._info('Running command "%s"' % cmd)
        child = Popen(cmd, shell=True, stdout=PIPE)
        output = child.communicate()[0]

        self._trace('output = %s' % output)
        self._trace('rc = %s' % child.returncode)

        return output, child.returncode

    def _run_ipmitool_checked(self, cmd):
        output, rc = self._run_ipmitool(cmd)
        if rc != 0:
            raise AssertionError('return code was %d' % rc)
        return output

    def clear_activation_lock_bit(self, fruid=0):
        """Clears the activation lock bit for to the given FRU.
        """
        fruid = int(fruid)
        self._run_ipmitool_checked('picmg policy set %d 1 0' % fruid)

    def clear_deactivation_lock_bit(self, fruid=0):
        """Clears the deactivation lock bit for to the given FRU.
        """
        fruid = int(fruid)
        self._run_ipmitool_checked('picmg policy set %d 2 0' % fruid)

    def issue_frucontrol_cold_reset(self, fruid=0):
        """Sends a _frucontrol cold reset_ to the given FRU.
        """
        fruid = int(fruid)
        self._run_ipmitool_checked('picmg frucontrol %d 0' % fruid)

    def issue_chassis_power_cycle(self):
        """Sends a _chassis power cycle_.
        """
        self._run_ipmitool_checked('chassis power cycle')

    def set_timeout(self, timeout):
        """Sets the timeout used in `Wait Until X` keywords to the given value.

        `timeout` is given in Robot Framework's time format
        (e.g. 1 minute 20 seconds) that is explained in the User Guide.

        The old timeout is returned and can be used to restore it later.

        Example.
        | ${tout}= | Set Timeout | 2 minute 30 seconds |
        | Do Something |
        | Set Timeout | ${tout} |
        """

        old = getattr(self, '_timeout', 3.0)
        self._timeout = utils.timestr_to_secs(timeout)
        return utils.secs_to_timestr(old)

    def set_poll_interval(self, poll_interval):
        """Sets the poll interval used in `Wait Until X` keywords to the given
        value.

        `poll_interval` is given in Robot Framework's time format.
        
        The old poll interval is returend.

        For more details see `Set Timeout`.
        """
        old = getattr(self, '_poll_interval', 1.0)
        self._poll_interval = utils.timestr_to_secs(poll_interval)
        return utils.secs_to_timestr(old)

    def clear_sel(self):
        """Clears the SEL.
        """
        self._run_ipmitool_checked('sel clear')

    def fetch_sel(self):
        """Fetches the SEL.
        
        Fetching the SEL is required for all further operation on the SEL.

        See `Sel Should Contain X Times Sensor Type`, `Select Sel Record By
        Sensor Type` and `Wait Until Sel Contains Sensor Type`.
        """
        del self._sel_records[:]
        output = self._run_ipmitool_checked('sel list -vv')
        for line in output.split('\n'):
            if line.startswith('SEL Entry: '):
                hexdata = line[11:].strip()
                record = SelRecord()
                record.decode_hex(hexdata)
                self._sel_records.append(record)

        print '*DEBUG* Parsed SEL Records (%d)' % len(self._sel_records)
        for record in self._sel_records:
            print record

    def _find_sel_records_by_sensor_type(self, type):
        matches = []
        for record in self._sel_records:
            if record.sensor_type == type:
                matches.append(record)
        return matches

    def _find_sensor_type(self, type):
        return find_attribute(SelRecord, type, 'SENSOR_TYPE_')

    def sel_should_contain_x_entries(self, count, msg=None):
        """Fails if the SEL does not contain `count` entries.
        """
        count = int(count)
        asserts.fail_unless_equal(count, len(self._sel_records), msg)

    def sel_should_contain_x_times_sensor_type(self, type, count, msg=None):
        """Fails if the SEL does not contain `count` times an event with the
        given sensor type.
        """

        type = self._find_sensor_type(type)
        count = int(count)

        records = self._find_sel_records_by_sensor_type(type)
        asserts.fail_unless_equal(count, len(records), msg)

    def sel_should_not_contain_sensor_type(self, type, msg=None):
        """Fails if SEL contains the given sensor type.
        """

        type = self._find_sensor_type(self, type)
        records = self._find_sel_records_by_sensor_type(self, type)
        if len(records) != 0:
            raise AssertionError('SEL contains sensor type %s' % type)

    def wait_until_sel_contains_x_times_sensor_type(self, count, type):
        type = self._find_sensor_type(type)

        count = int(count)

        start_time = time.time()
        while time.time() < start_time + self._timeout:
            self.fetch_sel()
            records = self._find_sel_records_by_sensor_type(type)
            if len(records) >= count:
                self._selected_sel_record = records[0]
                return
            time.sleep(self._poll_interval)

        raise AssertionError('No match found for SEL record type "%s" in %s.'
                % (type, utils.secs_to_timestr(self._timeout)))


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

        type = self._find_sensor_type(type)
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

        # apply mask
        expected_value = expected_value & mask
        value = self._selected_sel_record.event_data & mask

        if not self._selected_sel_record:
            raise RuntimeError('No SEL record selected.')
        asserts.fail_unless_equal(expected_value, value, msg)

    def _find_event_direction(self, direction):
        return find_attribute(SelRecord, direction, 'EVENT_')

    def selected_sel_records_event_direction_should_be(self,
            expected_direction, msg=None):
        direction = self._find_event_direction(expected_direction)
        asserts.fail_unless_equal(direction,
                self._selected_sel_record.event_direction, msg)

    def _get_sensor_list(self):
        output = self._run_ipmitool_checked('sensor list')
        sensor_list = []
        for line in output.split('\n'):
            # skip empty lines
            if not line.strip():
                continue

            data = line.split('|', 10)
            # skip not matching line
            if len(data) != 10:
                continue

            name = data[0].strip()
            type = data[2].strip()


            if (type == 'discrete'):
                try:
                    value = int(data[1].strip(), 16)
                except ValueError:
                    value = None
                try:
                    state = int(data[3].strip(), 16)
                    # swap bytes and mask MSB
                    state = ((state >> 8) & 0xff) | ((state << 16) & 0xff)
                except ValueError:
                    state = None
            else:
                try:
                    value = float(data[1].strip())
                except:
                    value = None
                state = data[3].strip()
                if state == "na":
                    state = None
            sensor_list.append((name, value, state))
            self._trace('sensor "%s" value "%s" state "%s"' %
                    (name, value, state))

        return sensor_list

    def _find_sensor_by_name(self, name):
        sensors = self._get_sensor_list()
        for sensor in sensors:
            if sensor[0] == name:
                return sensor

    def get_sensor_value(self, name):
        name = str(name)

        sensor = self._find_sensor_by_name(name)
        if not sensor:
            raise RuntimeError('No sensor found with name "%s"', name)
        return sensor[1]

    def get_sensor_state(self, name):
        name = str(name)

        sensor = self._find_sensor_by_name(name)
        if not sensor:
            raise RuntimeError('No sensor found with name "%s"', name)
        return sensor[2]

    def sensor_value_should_be(self, name, expected_value, msg=None):
        expected_value = int_any_base(expected_value)
        current_value = self.get_sensor_value(name)
        asserts.fail_unless_equal(expected_value, current_value, msg)

    def sensor_state_should_be(self, name, expected_state, msg=None):
        expected_state = int_any_base(expected_state)
        current_state = self.get_sensor_state(name)
        asserts.fail_unless_equal(expected_state, current_state, msg)

    def wait_until_sensor_state_is(self, name, state):
        """Wait until a sensor reaches the given state.
        """
        
        name = str(name)
        state = int_any_base(state)

        start_time = time.time()
        while time.time() < start_time + self._timeout:
            current_state = self.get_sensor_state(name)
            if current_state == state:
                return
            time.sleep(self._poll_interval)

        raise AssertionError('Sensor "%s" did not reach the state "%s" in %s.'
                % (name, state, utils.secs_to_timestr(self._timeout)))

    def wait_until_sensor_value_is(self, name, value):
        """Wait until a sensor reaches the given value.
        """
        
        name = str(name)
        state = int_any_base(state)

        start_time = time.time()
        while time.time() < start_time + self._timeout:
            current_value = self.get_sensor_value(name)
            if current_value == value:
                return
            time.sleep(self._poll_interval)

        raise AssertionError('Sensor "%s" did not reach the value "%s" in %s.'
                % (name, state, utils.secs_to_timestr(self._timeout)))

    def set_sensor_threshold(self, name, threshold, value):
        """Set specified threshold of sensor to value
        
        Example:

        """
        name = str(name)
        threshold = str(threshold)
        value = int(value)
        
        self._run_ipmitool_checked('sensor thresh "%s" "%s" %d' % (name, threshold, value) )


    def _warn(self, msg):
        self._log(msg, 'WARN')

    def _info(self, msg):
        self._log(msg, 'INFO')

    def _debug(self, msg):
        self._log(msg, 'DEBUG')

    def _trace(self, msg):
        self._log(msg, 'TRACE')

    def _log(self, msg, level=None):
        self._is_valid_log_level(level, raise_if_invalid=True)
        msg = msg.strip()
        if level is None:
            level = self._default_log_level
        if msg != '':
            print '*%s* %s' % (level.upper(), msg)

    def _is_valid_log_level(self, level, raise_if_invalid=False):
        if level is None:
            return True
        if isinstance(level, basestring) and \
                level.upper() in ['TRACE', 'DEBUG', 'INFO', 'WARN', 'HTML']:
            return True
        if not raise_if_invalid:
            return False
        raise AssertionError("Invalid log level '%s'" % level)

