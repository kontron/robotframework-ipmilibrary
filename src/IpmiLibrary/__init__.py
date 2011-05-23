#
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
# author: Heiko Thiery <heiko.thiery@kontron.com>
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

from sdr import Sdr
from sel import Sel

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


class IpmiConnection():
    def __init__(self, ipmi):
        self._ipmi = ipmi
        self._sel_records = []
        self._selected_sel_record = None
        self._sdr_list = []
        self._selected_sdr = None
        self._fru_data = None


class IpmiLibrary(Sdr, Sel):
    def __init__(self, timeout=3.0, poll_interval=1.0):
        self._cache = ConnectionCache()
        self._timeout = timeout
        self._poll_interval = poll_interval

    def wait_until_rmcp_is_ready(self, host, timeout=45):
        """Waits until the host can handle RMCP packets.

        `timeout` is given in Robot Framework's time format
        (e.g. 1 minute 20 seconds) that is explained in the User Guide.
        """

        timeout = utils.timestr_to_secs(timeout)

        start_time = time.time()
        while time.time() < start_time + timeout:
            try:
                self._active_connection._ipmi.session.rmcp_ping()
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

        connection = IpmiConnection(ipmi)

        self._active_connection = connection

        return self._cache.register(connection, alias)

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
        self._active_connection.ipmi.session.close()

    def wait_until_connection_is_ready(self):
        ac = self._active_connection
        start_time = time.time()
        while time.time() < start_time + self._timeout:
            output, rc = ac._ipmi.interface._run_ipmitool(
                    ac._ipmi.target, 'bmc info')
            if rc != 0:
                time.sleep(self._poll_interval)
            else:
                return

    def _run_ipmitool_checked(self, cmd):
        ac = self._active_connection
        output, rc = ac._ipmi.interface._run_ipmitool(
                ac._ipmi.target, cmd)
        if rc != 0:
            raise AssertionError('return code was %d' % rc)
        return output

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
        ac = self._active_connection
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
        ac = self._active_connection
        old = getattr(self, '_poll_interval', 1.0)
        self._poll_interval = utils.timestr_to_secs(poll_interval)
        return utils.secs_to_timestr(old)

    def ipmi_command_should_return_with_completion_code(self, netfn, lun,
                command_id, cc, msg=None):
        """
        """
        netfn = int_any_base(netfn)
        lun = int_any_base(lun)
        command_id = int_any_base(command_id)
        cc = int_any_base(cc)

        m = pyipmi.msgs.bmc.RawMessage()
        m.NETFN = netfn
        m.LUN = lun
        m.CMDID = command_id

        self._active_connection._ipmi._send_and_receive(m)
        asserts.fail_unless_equal(cc, m.rsp.completion_code, msg)

    def issue_bmc_cold_reset(self):
        """Sends a _bmc cold reset_ to the given controler.
        """
        self._active_connection._ipmi.cold_reset()

    def get_bmc_device_id(self):
        """Sends a _bmc get device id_ command to the given controller.
        """
        self._run_ipmitool_checked('raw 6 1')

    def clear_activation_lock_bit(self, fruid=0):
        """Clears the activation lock bit for to the given FRU.
        """
        fruid = int(fruid)
        self._active_connection._ipmi.clear_fru_activation_lock(fruid)

    def clear_deactivation_lock_bit(self, fruid=0):
        """Clears the deactivation lock bit for to the given FRU.
        """
        fruid = int(fruid)
        self._active_connection._ipmi.clear_fru_deactivation_lock(fruid)

    def issue_frucontrol_cold_reset(self, fruid=0):
        """Sends a _frucontrol cold reset_ to the given FRU.
        """
        fruid = int(fruid)
        self._active_connection._ipmi.fru_control_cold_reset(fruid)

    def issue_frucontrol_diagnostic_interrupt(self, fruid=0):
        """Sends a _frucontrol diagnostic interrupt_ to the given FRU.
        """
        fruid = int(fruid)
        self._active_connection._ipmi.fru_control_diagnostic_interrupt(fruid)

    def issue_chassis_power_down(self):
        """Sends a _chassis power down_ command.
        """
        self._active_connection._ipmi.chassis_control_power_down()

    def issue_chassis_power_cycle(self):
        """Sends a _chassis power cycle_.
        """
        self._active_connection._ipmi.chassis_control_power_cycle()

    def issue_chassis_power_reset(self):
        """Sends a _chassis power reset_.
        """
        self._active_connection._ipmi.chassis_control_hard_reset()

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

    def _find_sel_records_by_sensor_type(self, type):
        ac = self._active_connection
        matches = []
        for record in ac._sel_records:
            if record.sensor_type == type:
                matches.append(record)
        return matches

    def _find_sel_records_by_sensor_number(self, number):
        ac = self._active_connection
        matches = []
        for record in ac._sel_records:
            if record.sensor_number == number:
                matches.append(record)
        return matches

    def sel_should_contain_x_entries(self, count, msg=None):
        """Fails if the SEL does not contain `count` entries.
        """
        ac = self._active_connection
        count = int(count)
        asserts.fail_unless_equal(count, len(ac._sel_records), msg)

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
        ac = self._active_connection
        type = find_sensor_type(type)
        count = int(count)

        start_time = time.time()
        while time.time() < start_time + self._timeout:
            self.fetch_sel()
            records = self._find_sel_records_by_sensor_type(type)
            if len(records) >= count:
                ac._selected_sel_record = records[0]
                return
            time.sleep(self._poll_interval)

        raise AssertionError('No match found for SEL record type "%s" in %s.'
                % (type, utils.secs_to_timestr(self._timeout)))


    def wait_until_sel_contains_x_times_sensor_number(self, count, number):
        ac = self._active_connection
        number = find_sensor_type(number)
        count = int(count)

        start_time = time.time()
        while time.time() < start_time + self._timeout:
            self.fetch_sel()
            records = self._find_sel_records_by_sensor_number(number)
            if len(records) >= count:
                ac._selected_sel_record = records[0]
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
            self._active_connection._selected_sel_record = records[index]
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
            self._active_connection._selected_sel_record = records[index]
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
        ac = self._active_connection

        # apply mask
        expected_value = expected_value & mask
        value = (ac._selected_sel_record.event_data[0] << 16 |
                 ac._selected_sel_record.event_data[1] << 8 |
                 ac._selected_sel_record.event_data[2])
        value = value & mask

        if not ac._selected_sel_record:
            raise RuntimeError('No SEL record selected.')
        asserts.fail_unless_equal(expected_value, value, msg)

    def selected_sel_records_event_direction_should_be(self,
            expected_direction, msg=None):
        direction = find_event_direction(expected_direction)
        ac = self._active_connection
        asserts.fail_unless_equal(direction,
                ac._selected_sel_record.event_direction, msg)

    def selected_sel_record_should_be_from_sensor_number(self, sensor_number,
             msg=None):
        """
        """
        sensor_number = int_any_base(sensor_number)

        if not self._selected_sel_record:
            raise RuntimeError('No SEL record selected.')
        asserts.fail_unless_equal(sensor_number,
                self._selected_sel_record.sensor_number, msg)

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
        ac = self._active_connection

        fru_id = int(fru_id)
        led_id = int(led_id)

        ac._led = ac.ipmi.get_led_state(fru_id, led_id)

        self._debug('LED state %s' % ac._led)

    def led_color_should_be(self, expected_color, msg=None, values=True):
        ac = self._active_connection
        expected_color = find_picmg_led_color(expected_color)
        if ac._led.override_enabled:
            color = ac._led.override_color
        else:
            color = ac._led.local_color
        asserts.fail_unless_equal(expected_color, color, msg, values)

    def led_function_should_be(self, expected_function, msg=None, values=True):
        ac = self._active_connection
        expected_function = find_picmg_led_function(expected_function)
        if ac._led.override_enabled:
            function = ac._led.override_function
        else:
            function = ac._led.local_function
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
        ac = self._active_connection

        link_info = pyipmi.picmg.LinkInfo()
        link_info.interface = find_picmg_interface_type(interface)
        link_info.channel = int(channel)
        link_info.link_flags = find_picmg_link_flags(flags)
        link_info.type = find_picmg_link_type(link_type)
        link_info.extension = find_picmg_link_type_extension(link_type_ext)
        link_info.state = find_picmg_link_state(state)
        link_info.grouping_id = 0
        ac._ipmi.set_port_state(link_info)

    def set_signaling_class(self, interface, channel, signaling_class):
        """Sends the `Set Channel Siganling Class` command.

        `interface` the interface type (BASE, FABRIC, UPDATE_CHANNEL)

        `channel` is the interface channel ID.

        `class` is the channel signaling class capability and hast to be one of
        the following values: CLASS_BASIC, CLASS_10_3125GBD.
        """
        ac = self._active_connection

        interface = find_picmg_interface_type(interface)
        channel = int(channel)
        signaling_class = find_picmg_signaling_class(signaling_class)
        ac._ipmi.set_signaling_class(interface, channel, signaling_class)

    def get_signaling_class(self, interface, channel):
        """Sends `Get Channel Signaling Class` command
        """
        ac = self._active_connection

        interface = find_picmg_interface_type(interface)
        channel = int(channel)
        ac._ipmi.get_signaling_class(interfac, channel)

    def start_watchdog_timer(self, value, action):
        """Sets and starts IPMI watchdog timer.

        The watchdog is set to `value` and after that it is started.

        The maximum value is 6553 seconds. `value` is given in Robot
        Framework's time format (e.g. 1 minute 20 seconds) that is explained in
        the User Guide.
        """
        ac = self._active_connection

        config = pyipmi.bmc.Watchdog()
        config.timer_use = pyipmi.bmc.Watchdog.TIMER_USE_SMS_OS
        config.dont_stop = 1
        config.dont_log = 0
        config.pre_timeout_interval = 0
        config.pre_timeout_interrupt = 0
        config.timer_use_expiration_flags = 8
        # convert to 100ms
        config.initial_countdown = int(utils.timestr_to_secs(value) * 10)
        if (config.initial_countdown > 0xffff):
            raise RuntimeError('Watchdog value out of range')
        config.timeout_action = find_watchdog_action(action)
        # set watchdog
        ac._ipmi.set_watchdog_timer(config)
        # start watchdog
        ac._ipmi.reset_watchdog_timer()

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

    def send_raw_command(self, *bytes):
        """Sends a raw IPMI command.

        `bytes` can either be a list or serveral scalar values.
        If a LUN other then zero is needed, it can be given with the first
        value of the list by prepending 'lun=', eg. lun=3.

        Example:
        | ${values}= | Set Variable | 0x06 | 0x01 | |
        | Send Raw Command | ${values} |  |  | | # BMC info command
        | Send Raw Command | 0x06 | 0x01 | | | # same as above
        | Send Raw Command | lun=3 | 0x3e | 0x62 | ... | # LUN other than zero
        """
        raise RuntimeError('implementation needed :)')

    def fetch_fru_data(self, fru_id=0):
        """Fetches the FRU data of the given `fru_id`.
        Fetching the FRU data is required for all further operation on the FRU
         data
        """
        ac = self._active_connection
        ac._fru_data = ac._ipmi.read_fru_data(fru_id)

    def fru_data_byte_at_offset_should_be(self, offset, value, msg=None):
        """Fails if the FRU data does not contain `value` at the given `offset`
        """
        ac = self._active_connection
        offset = int_any_base(offset)
        value = int_any_base(value)

        if ac._fru_data is None:
            self.fetch_fru_data()

        asserts.fail_unless_equal(value, ord(ac._fru_data.data[offset]), msg)

    def fru_data_bytes_at_offset_should_be(self, offset, length,
                value_expected, msg=None, order='lsb'):
        """Fails if the FRU data does not contain `value` at the given `offset`
        """
        ac = self._active_connection
        offset = int_any_base(offset)
        length = int_any_base(length)
        value_expected = int_any_base(value_expected)

        if ac._fru_data is None:
            self.fetch_fru_data()

        value = 0
        if order == 'lsb':
            for v in ac._fru_data.data[offset+length-1:offset-1:-1]:
                value = (value << 8) + ord(v)
        elif order == 'msb':
            for v in ac._fru_data.data[offset:offset+length]:
                value = (value << 8) + ord(v)
        else:
            raise RuntimeError('Unknown order')

        asserts.fail_unless_equal(value_expected, value, msg)

    def fru_data_tlv_at_offset_should_be(self, offset, expected_type,
                expected_length, expected_value, msg=None):
        ac = self._active_connection
        offset = int_any_base(offset)
        expected_type = find_fru_field_type_code(expected_type)
        expected_length = int_any_base(expected_length)

        if ac._fru_data is None:
            self.fetch_fru_data()

        type = (ord(ac._fru_data.data[offset]) & 0xc0) >> 6
        asserts.fail_unless_equal(expected_type, type, 'type missmatch')

        length = ord(ac._fru_data.data[offset]) & 0x3f
        asserts.fail_unless_equal(expected_length, length, 'length missmatch')

        value = None
        if expected_type == 0:
            expected_value = int_any_base(expected_value)
            slice = ac._fru_data.data[offset+1:offset+length+1]
            value = 0
            for v in slice:
                value = (value << 8) + ord(v)
        elif expected_type == 3:
            value = ac._fru_data.data[offset+1:offset+length+1]
        else:
            raise RuntimeError('type %s not supported' % expected_type)

        asserts.fail_unless_equal(expected_value, value, 'value missmatch')

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

