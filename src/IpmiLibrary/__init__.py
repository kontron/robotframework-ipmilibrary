#
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
#

import logging
import time
from sel import SelRecord
from subprocess import Popen, PIPE

from robot import utils
from robot.utils import asserts
from robot.utils.connectioncache import ConnectionCache
from robot.output import LOGGER
from robot.output.loggerhelper import Message
import pyipmi
import pyipmi.logger
import pyipmi.interfaces

from utils import int_any_base
from mapping import *

class RobotLogHandler(logging.Handler):
    # mappping from logging to robots log levels
    mapping = {
            'NOTSET'   : 'NONE',
            'DEBUG'    : 'DEBUG',
            'INFO'     : 'INFO',
            'WARNING'  : 'WARN',
            'ERROR'    : 'ERROR',
            'CRITICAL' : 'ERROR',
    }
    def __init__(self):
        logging.Handler.__init__(self)
        # format it the way robotframework understands it
        self.setFormatter(logging.Formatter("*%(levelname)s* %(message)s"))
    def emit(self, record):
        msg = record.getMessage()
        lvl = self.mapping[record.levelname]
        LOGGER.log_message(Message(msg, lvl))

# add log handler to pyipmi
pyipmi.logger.add_log_handler(RobotLogHandler())
pyipmi.logger.set_log_level(logging.DEBUG)


class TimeoutError(Exception):
    pass


class IpmiLibrary:
    def __init__(self, timeout=3.0, poll_interval=1.0):
        self._sel_records = []
        self._selected_sel_record = None
        self.set_timeout(timeout)
        self.set_poll_interval(poll_interval)
        self._cache = ConnectionCache()

    def _rmcp_ping(self, host):
        # for now this uses impitool..
        cmd = self.IPMITOOL
        cmd += (' -I lan')
        cmd += (' -H %s' % host)
        cmd += (' -A NONE')
        cmd += (' session info all')

        self._info('Running command "%s"' % cmd)
        child = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        child.communicate()

        self._trace('rc = %s' % child.returncode)
        if child.returncode:
            raise TimeoutError()

    def wait_until_rmcp_is_ready(self, host, timeout=45):
        """Waits until the host can handle RMCP packets.

        `timeout` is given in Robot Framework's time format
        (e.g. 1 minute 20 seconds) that is explained in the User Guide.
        """

        timeout = utils.timestr_to_secs(timeout)

        start_time = time.time()
        while time.time() < start_time + timeout:
            try:
                self._rmcp_ping(host)
                return
            except TimeoutError:
                pass

        raise AssertionError('RMCP not ready in %s.'
                % (utils.secs_to_timestr(timeout)))

    def open_ipmi_connection(self, host, target_address, user='', password='',
            routing_information=[(0x20,0)], interface='ipmitool', alias=None):
        """Opens a LAN connection to an IPMI shelf manager.
 
        `host` is the IP or hostname of the shelf manager. `target_address` the
        IPMI address to which the command should be sent. `user` and `password`
        are used to authenticate against the shelf manager.
        """

        host = str(host)
        target_address = int_any_base(target_address)
        user = str(user)
        password = str(password)

        if alias:
            alias = str(alias)

        interface = pyipmi.interfaces.create_interface(interface)
        ipmi = pyipmi.create_connection(interface)
        ipmi.session.set_session_type_rmcp(host)
        ipmi.session.set_auth_type_user(user, password)
        ipmi.target = pyipmi.Target(target_address)
        ipmi.target.set_routing_information(routing_information)

        self._info('Opening IPMI connection to %s:%s' % (host,
            target_address))

        ipmi.session.establish()

        self._active_connection = ipmi

        return self._cache.register(ipmi, alias)

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
        self._active_connection.session.close()

    def wait_until_connection_is_ready(self):
        start_time = time.time()
        while time.time() < start_time + self._timeout:
            output, rc = self._run_ipmitool('bmc info')
            if rc != 0:    
                time.sleep(self._poll_interval)
            else:
                return
        
    def _run_ipmitool_checked(self, cmd):
        output, rc = self._active_connection.interface._run_ipmitool(
                self._active_connection.target, cmd)
        if rc != 0:
            raise AssertionError('return code was %d' % rc)
        return output

    def issue_bmc_cold_reset(self, fruid=0):
        """Sends a _bmc cold reset_ to the given controler.
        """
        self._run_ipmitool_checked('raw 6 2')

    def get_bmc_device_id(self):
        """Sends a _bmc get device id_ command to the given controler.
        """
        self._run_ipmitool_checked('raw 6 1')

    def clear_activation_lock_bit(self, fruid=0):
        """Clears the activation lock bit for to the given FRU.
        """
        fruid = int(fruid)
        self._active_connection.clear_fru_activation_lock(fruid)

    def clear_deactivation_lock_bit(self, fruid=0):
        """Clears the deactivation lock bit for to the given FRU.
        """
        fruid = int(fruid)
        self._active_connection.set_fru_deactivation_lock(fruid)
        
    def issue_frucontrol_cold_reset(self, fruid=0):
        """Sends a _frucontrol cold reset_ to the given FRU.
        """
        self._active_connection.fru_control_cold_reset(fruid)

    def issue_frucontrol_diagnostic_interrupt(self, fruid=0):
        """Sends a _frucontrol diagnostic interrupt_ to the given FRU.
        """
        self._active_connection.fru_control_diagnostic_interrupt(fruid)

    def issue_chassis_power_down(self):
        """Sends a _chassis power down_ command.
        """
        self._run_ipmitool_checked('chassis power down')

    def issue_chassis_power_cycle(self):
        """Sends a _chassis power cycle_.
        """
        self._run_ipmitool_checked('chassis power cycle')

    def issue_chassis_power_reset(self):
        """Sends a _chassis power reset_.
        """
        self._run_ipmitool_checked('chassis power reset')

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

    def sel_should_contain_x_entries(self, count, msg=None):
        """Fails if the SEL does not contain `count` entries.
        """
        count = int(count)
        asserts.fail_unless_equal(count, len(self._sel_records), msg)

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

    def selected_sel_records_event_direction_should_be(self,
            expected_direction, msg=None):
        direction = find_event_direction(expected_direction)
        asserts.fail_unless_equal(direction,
                self._selected_sel_record.event_direction, msg)

    def selected_sel_record_should_be_from_sensor_number(self, sensor_number,
             msg=None):
        """
        """
        sensor_number = int_any_base(sensor_number)

        if not self._selected_sel_record:
            raise RuntimeError('No SEL record selected.')
        asserts.fail_unless_equal(sensor_number,
                self._selected_sel_record.sensor_number, msg)

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
                thresholds = None
            else:
                thresholds = {}
                # get sensor reading
                try:
                    value = float(data[1].strip())
                except ValueError:
                    value = None

                # get sensor state
                state = data[3].strip()
                if state == "na":
                    state = None

                # get sensor thresholds
                #for (i, t) in enumerate(('lnr', 'lcr', 'lnc', 'unc', 'ucr', 'unr'), start=4):
                for (i, t) in enumerate(('lnr', 'lcr', 'lnc', 'unc', 'ucr',
                        'unr')):
                    try:
                        thresholds[t] = float(data[i+4].strip())
                    except ValueError:
                        pass

            sensor_list.append((name, value, state, thresholds))
            self._trace('sensor "%s" value "%s" state "%s" threshs "%s"' %
                    (name, value, state, thresholds))

        return sensor_list

    def _find_sensor_by_name(self, name):
        sensors = self._get_sensor_list()
        for sensor in sensors:
            if sensor[0] == name:
                return sensor

    def get_sensor_reading(self, name):
        """Returns a sensor reading.

        `name` is the sensor ID string given in the SDR.
        """

        name = str(name)

        sensor = self._find_sensor_by_name(name)
        if not sensor:
            raise RuntimeError('No sensor found with name "%s"' % name)
        return sensor[1]

    def get_sensor_state(self, name):
        """Returns the assertion state of a sensor.

        `name` is the sensor ID string. See also `Get Sensor Reading`.
        """
        name = str(name)

        sensor = self._find_sensor_by_name(name)
        if not sensor:
            raise RuntimeError('No sensor found with name "%s"' % name)
        return sensor[2]

    def _get_sensor_thresholds(self, name):
        name = str(name)
        sensor =  self._find_sensor_by_name(name)
        if not sensor:
            raise RuntimeError('No sensor found with name "%s"' % name)
        return sensor[3]
    
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
        thresholds = self._get_sensor_thresholds(name)
        if not thresholds:
            raise RuntimeError('No thresholds for sensor with name "%s"' % name)
        
        try:
            return thresholds[threshold] 
        except KeyError:
            raise RuntimeError('Threshold "%s" not found for sensor "%s"' %
                    (threshold, name))

    def sensor_value_should_be(self, name, expected_value, msg=None):
        """Fails unless the sensor value has the expected value.

        `name` is the sensor ID string. See also `Get Sensor Reading`.
        """

        expected_value = int_any_base(expected_value)
        current_value = self.get_sensor_value(name)
        asserts.fail_unless_equal(expected_value, current_value, msg)

    def sensor_state_should_be(self, name, expected_state, msg=None):
        """Fails unless the sensor state has the expected state.

        `name` is the sensor ID string. See also `Get Sensor Reading`.
        """

        expected_state = int_any_base(expected_state)
        current_state = self.get_sensor_state(name)
        asserts.fail_unless_equal(expected_state, current_state, msg)

    def wait_until_sensor_state_is(self, name, state):
        """Wait until a sensor reaches the given state.

        `name` is the sensor ID string. See also `Get Sensor Reading`.
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

        `name` is the sensor ID string. See also `Get Sensor Reading`.
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
        """Sets the threshold of a sensor.

        For the `name` and `threshold` parameters see `Get Sensor Threshold`.
        """

        name = str(name)
        threshold = str(threshold)
        value = float(value)
       
        self._run_ipmitool_checked('sensor thresh "%s" "%s" %f' % (name, threshold, value) )

    def picmg_get_led_state(self, fru_id, led_id):
        """Returns the FRU LED state.
        """
        fru_id = int(fru_id)
        led_id = int(led_id)

        self._led = self._active_connection.get_led_state(fru_id, led_id)

        self._debug('LED state %s' % self._led)

    def led_color_should_be(self, expected_color, msg=None, values=True):
        expected_color = find_picmg_led_color(expected_color)
        if self._led.override_enabled:
            color = self._led.override_color
        else:
            color = self._led.local_color
        asserts.fail_unless_equal(expected_color, color, msg, values)
  
    def led_function_should_be(self, expected_function, msg=None, values=True):
        expected_function = find_picmg_led_function(expected_function)
        if self._led.override_enabled:
            function = self._led.override_function
        else:
            function = self._led.local_function
        asserts.fail_unless_equal(expected_function, function, msg, values)
 
    def set_port_state(self, interface, channel, flags, link_type,
            link_type_ext, state):
        """Sends the "PICMG Set Portstate" command.

        `interface` is one of the following interface types: BASE, FABRIC,
        UPDATE_CHANNEL.

        `channel` is the interface channel ID. `flags` is the lane mask and one
        of the following values: LANE0, LANE0123.

        `link_type` is one of the following values: BASE, ETHERNET_FABRIC,
        INFINIBAND_FABRIC, STARFABRIC_FABRIC, PCIEXPRESS_FABRIC.

        `link_type_ext` is one of the following values: BASE0, BASE1,
        ETHERNET_FIX1000BX, ETHERNET_FIX10GBX4, ETHERNET_FCPI,
        ETHERNET_FIX1000KX_10GKR, ETHERNET_FIX10GKX4, ETHERNET_FIX40GKR4

        `state` is the link state and has to be one of the following values:
        ENABLE, DISABLE.

        Note: Link Grouping ID is not supported yet

        Example:
        | Set Port State | BASE | 1 | LANE0 | BASE | BASE0 | ENABLE
        """

        link_info = LinkInfo()
        link_info.interface = find_picmg_interface_type(interface)
        link_info.channel = int(channel)
        link_info.flags = find_picmg_link_flags(flags)
        link_info.link_type = find_picmg_link_type(link_type)
        link_info.extension = find_picmg_link_type_extension(link_type_ext)
        link_info.state = find_picmg_link_state(state)
        link_info.group_id = 0
        self._active_connection.set_port_state(link_info)

    def set_signaling_class(self, interface, channel, signaling_class):
        """Sends the `Set Channel Siganling Class` command.

        `interface` the interface type (BASE, FABRIC, UPDATE_CHANNEL)

        `channel` is the interface channel ID.

        `class` is the channel signaling class capability and hast to be one of
        the following values: CLASS_BASIC, CLASS_10_3125GBD.
        """

        interface = find_picmg_interface_type(interface)
        channel = int(channel)
        signaling_class = find_picmg_signaling_class(signaling_class)
        self._active_connection.set_signaling_class(interface, channel, 
                signaling_class)

    def get_signaling_class(self, interface, channel):
        """Sends `Get Channel Signaling Class` command
        """
        
        interface = find_picmg_interface_type(interface)
        channel = int(channel)
        self._active_connection.get_signaling_class(interfac, channel)

    def start_watchdog_timer(self, value, action):
        """Sets and starts IPMI watchdog timer.

        The watchdog is set to `value` and after that it is started.

        The maximum value is 6553 seconds. `value` is given in Robot
        Framework's time format (e.g. 1 minute 20 seconds) that is explained in
        the User Guide.
        """
        value = utils.timestr_to_secs(value)
        value = int(value * 10) # convert to 100ms steps 
        if (value > 0xffff):
            raise RuntimeError('Watchdog value out of range')
        value_lsb = value & 0xff
        value_msb = (value >> 8) & 0xff
        timer_use = 4
        timer_action = find_watchdog_action(action)
        pre_timeout_interval = 0
        timer_use_exp_flags_clear = 8
        # set watchdog
        cmd = 'raw 6 0x24 %d %d %d %d %d %d' % \
            (timer_use, timer_action, pre_timeout_interval, \
                timer_use_exp_flags_clear, value_lsb, value_msb)
        self._run_ipmitool_checked(cmd)
        # start watchdog
        cmd = 'raw 6 0x22'
        self._run_ipmitool_checked(cmd)

    def hpm_start_firmware_upload(self, file_path, filename):
        """
        """

        cmd = 'hpm upgrade %s/%s all' % (file_path, filename)
        self._run_ipmitool_checked(cmd)

    def hpm_start_firmware_activation(self):
        """
        """

        cmd = 'hpm activate'
        self._run_ipmitool_checked(cmd)

    def hpm_start_firmware_rollback(self):
        """
        """
        cmd = 'hpm rollback'
        self._run_ipmitool_checked(cmd)

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

